#!/usr/bin/env python3
"""bm.py — Chrome bookmark index and patch tool.

Stdlib only. Reads Chrome's Bookmarks JSON, maintains a sidecar index
(JSONL in git + SQLite FTS5 built locally), and applies reviewed patches
back to the Bookmarks file.

Data directory (default ~/.claude/bookmarks, override with BM_DATA_DIR):
    config.json    profile settings
    profile.md     personal taxonomy rules, read by the model
    index.jsonl    source of truth, one line per bookmark, committed to git
    index.db       FTS5 index built from index.jsonl, gitignored
    backups/       timestamped copies of Bookmarks, gitignored
"""

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import sqlite3
import socket
import subprocess
import sys
import threading
import time
import typing
import unicodedata
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

DATA_DIR = os.path.expanduser(os.environ.get("BM_DATA_DIR", "~/.claude/bookmarks"))
JSONL = os.path.join(DATA_DIR, "index.jsonl")
DB = os.path.join(DATA_DIR, "index.db")
CONFIG = os.path.join(DATA_DIR, "config.json")
BACKUPS = os.path.join(DATA_DIR, "backups")

WEBKIT_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc).timestamp()
ROOTS = ("bookmark_bar", "other", "synced")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


# ---------------------------------------------------------------- helpers

def die(msg, code=1) -> typing.NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


# Defaults are starting points, not judgements. The setup interview replaces them
# with numbers that match how the user actually keeps their bookmarks.
DEFAULT_THRESHOLDS = {
    "cold_days": 1095,       # never opened and older than this -> raise for review
    "thin_folder_max": 2,    # leaf folder with at most this many bookmarks -> collapse
    "deep_level": 5,         # bookmarks at this depth or deeper -> too many clicks
    "fat_folder_min": 21,    # folder with at least this many direct bookmarks -> split
    "hot_ttl_days": 180,     # time something may sit in the staging root
}

_CFG = None


def config():
    """config.json, overlaid by an optional gitignored config.local.json."""
    global _CFG
    if _CFG is not None:
        return _CFG
    cfg = {}
    for path in (CONFIG, os.path.join(DATA_DIR, "config.local.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                cfg.update(json.load(fh))
    _CFG = cfg
    return cfg


def thresholds():
    cfg = config()
    raw = dict(DEFAULT_THRESHOLDS)
    raw.update(cfg.get("thresholds", {}))
    for key in DEFAULT_THRESHOLDS:  # tolerate flat keys
        if key in cfg:
            raw[key] = cfg[key]
    out = {}
    for key, default in DEFAULT_THRESHOLDS.items():
        try:
            out[key] = int(raw[key])
        except (TypeError, ValueError, KeyError):
            print(f"warning: threshold {key}={raw.get(key)!r} is not a number, "
                  f"using {default}", file=sys.stderr)
            out[key] = default
    return out


def bookmarks_path():
    cfg = config()
    if cfg.get("bookmarks_file"):
        return os.path.expanduser(cfg["bookmarks_file"])
    base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if not os.path.isdir(base):  # linux fallback
        base = os.path.expanduser("~/.config/google-chrome")
    profile = cfg.get("profile", "Default")
    return os.path.join(base, profile, "Bookmarks")


def account_bookmarks_path():
    """A signed-in Chrome keeps the live tree in AccountBookmarks; the classic
    Bookmarks file is then the device-only store and is usually empty. Return the
    account store only when it exists and actually holds bookmarks."""
    acct = os.path.join(os.path.dirname(bookmarks_path()), "AccountBookmarks")
    if os.path.exists(acct):
        try:
            with open(acct, encoding="utf-8") as fh:
                d = json.load(fh)
            if any((d.get("roots", {}).get(k) or {}).get("children") for k in ROOTS):
                return acct
        except (OSError, ValueError, KeyError):
            pass
    return None


def bookmarks_read_path():
    """Where the bookmarks actually are, for reading. Prefer the account store."""
    return account_bookmarks_path() or bookmarks_path()


def load_tree():
    p = bookmarks_read_path()
    if not os.path.exists(p):
        die(f"Bookmarks file not found: {p}")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh), p


def wk_to_unix(us):
    try:
        us = int(us)
    except (TypeError, ValueError):
        return None
    return None if us == 0 else WEBKIT_EPOCH + us / 1e6


def unix_to_wk(ts):
    return str(int((ts - WEBKIT_EPOCH) * 1e6))


def now_wk():
    return unix_to_wk(time.time())


def iso(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""


def days_ago(ts):
    return None if not ts else int((time.time() - ts) / 86400)


def walk(data):
    """Yield (node, path_list, parent_guid, root) for every node under the roots."""
    for root in ROOTS:
        node = data["roots"].get(root)
        if not node:
            continue
        stack = [(node, [root], None)]
        while stack:
            n, path, parent = stack.pop()
            yield n, path, parent, root
            for child in reversed(n.get("children", [])):
                stack.append((child, path + [child.get("name", "")], n.get("guid")))


def bookmarks(data):
    """Yield dicts for url nodes only."""
    for n, path, parent, root in walk(data):
        if n.get("type") != "url":
            continue
        yield {
            "guid": n.get("guid"),
            "id": n.get("id"),
            "title": n.get("name", ""),
            "url": n.get("url", ""),
            "path": path[:-1],
            "parent_guid": parent,
            "root": root,
            "added": wk_to_unix(n.get("date_added")),
            "used": wk_to_unix(n.get("date_last_used")),
        }


def folders(data):
    for n, path, parent, root in walk(data):
        if n.get("type") == "url":
            continue
        kids = n.get("children", [])
        yield {
            "guid": n.get("guid"),
            "name": n.get("name", ""),
            "path": path,
            "parent_guid": parent,
            "root": root,
            "n_urls": sum(1 for c in kids if c.get("type") == "url"),
            "n_folders": sum(1 for c in kids if c.get("type") != "url"),
        }


def pathstr(path):
    """Display form. Folder names may contain '/', so use a distinct separator."""
    return " › ".join(path)


TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "yclid", "mc_cid", "mc_eid", "igshid")


def normalize_url(url):
    """Identity for duplicate detection: scheme, www, case and tracking tails do
    not make a different page. Kept separate from the stored URL, which stays
    exactly as the user saved it."""
    try:
        parts = urlparse(url.strip())
    except ValueError:
        return url.strip().lower()
    host = parts.netloc.lower().removeprefix("www.")
    query = "&".join(
        p for p in parts.query.split("&")
        if p and not p.lower().startswith(TRACKING_PARAMS))
    path = parts.path.rstrip("/")
    return f"{host}{path}" + (f"?{query}" if query else "")


def domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


# ---------------------------------------------------------------- index io

def read_index():
    out = {}
    if not os.path.exists(JSONL):
        return out
    with open(JSONL, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                hint = ""
                if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
                    hint = ("\n  This is an unresolved git conflict marker. Records "
                            "are one line each and keyed by guid, so keeping both "
                            "sides and removing the markers is usually safe; then "
                            "run `bm.py sync`.")
                die(f"{JSONL} line {lineno} is not valid JSON: {line[:60]!r}\n"
                    f"  {exc}{hint}")
            out[rec["guid"]] = rec
    return out


def write_index(recs):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = JSONL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for guid in sorted(recs):
            fh.write(json.dumps(recs[guid], ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, JSONL)


def build_db(recs):
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE VIRTUAL TABLE bm USING fts5(
            guid UNINDEXED, path, title, url, tags, summary,
            tokenize = "unicode61 remove_diacritics 2",
            prefix = '2 3'
        );
        CREATE TABLE meta (
            guid TEXT PRIMARY KEY, parent_guid TEXT, root TEXT, path TEXT,
            title TEXT, url TEXT, domain TEXT, kind TEXT, summary TEXT,
            added TEXT, used TEXT, age_days INT,
            cold INT, evergreen INT, link TEXT, checked TEXT
        );
        CREATE TABLE meta_src (digest TEXT, size INT, records INT);
    """)
    for rec in recs.values():
        if rec.get("missing_since"):
            continue  # not in Chrome right now; keep the data, hide it from search
        con.execute(
            "INSERT INTO bm VALUES (?,?,?,?,?,?)",
            (rec["guid"], pathstr(rec.get("path", [])), rec.get("title", ""),
             rec.get("url", ""), " ".join(rec.get("tags", [])), rec.get("summary", "")))
        con.execute(
            "INSERT INTO meta VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec["guid"], rec.get("parent_guid", ""), rec.get("root", ""),
             pathstr(rec.get("path", [])), rec.get("title", ""), rec.get("url", ""),
             domain(rec.get("url", "")), rec.get("kind", ""), rec.get("summary", ""),
             rec.get("added", ""), rec.get("used", ""),
             rec.get("age_days") or 0, int(bool(rec.get("cold"))),
             int(bool(rec.get("evergreen"))), rec.get("link", ""),
             rec.get("checked", "")))
    # Fingerprint of the source, so search can tell a stale db from a fresh one —
    # `git pull` updates index.jsonl and never touches index.db.
    con.execute("INSERT INTO meta_src VALUES (?,?,?)", db_fingerprint(len(recs)))
    con.commit()
    con.close()


def jsonl_digest():
    """Content hash, not a timestamp — `cp -p` and `rsync -t` preserve mtime, and
    a same-size edit under a preserved mtime would otherwise look unchanged.
    Costs ~2ms on a 1.3MB index."""
    try:
        with open(JSONL, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return ""


def db_fingerprint(records):
    return (jsonl_digest(), 0, records)


def db_is_stale():
    """True when index.db no longer matches index.jsonl."""
    if not os.path.exists(DB) or not os.path.exists(JSONL):
        return True
    try:
        con = sqlite3.connect(DB)
        row = con.execute("SELECT digest FROM meta_src").fetchone()
        con.close()
    except sqlite3.Error:
        return True  # includes the pre-digest schema
    return not row or row[0] != jsonl_digest()


def content_key(title, url):
    """Identity of what was enriched, so an edited URL can be re-queued."""
    return hashlib.md5(f"{title}\x00{url}".encode("utf-8")).hexdigest()[:12]


def sync_records(data, recs, prune=False):
    """Refresh volatile fields from Chrome. Returns (new, gone, moved, stale).

    Every live bookmark gets a record even before enrichment, so search works
    on title/path/url from the first sync; enrichment only adds tags and summary.

    Records missing from Chrome are NOT dropped unless `prune` is set: a sync run
    against the wrong profile, or before Chrome sync has finished downloading,
    would otherwise delete the entire enrichment corpus in one step.
    """
    cfg = config()
    cold_days = thresholds()["cold_days"]
    hot_root = cfg.get("hot_folder")
    today = datetime.now().strftime("%Y-%m-%d")

    live = {b["guid"]: b for b in bookmarks(data)}
    new = [g for g in live if g not in recs]
    fresh = set(new)
    gone = [g for g in recs if g not in live]
    moved, stale = [], []

    for guid, b in live.items():
        rec = recs.setdefault(guid, {"guid": guid})
        if guid not in fresh and (rec.get("path") != b["path"]
                                  or rec.get("title") != b["title"]
                                  or rec.get("url") != b["url"]):
            moved.append(guid)
        # Enrichment describes the page, which is identified by its URL. A move or
        # a title cleanup keeps it valid; only an edited URL invalidates the tags.
        # (Comparing rec['url'] — last sync's value — before it is overwritten below.)
        if rec.get("tags") and rec.get("url") and rec["url"] != b["url"]:
            stale.append(guid)
            rec.pop("tags", None)
            rec.pop("summary", None)

        if hot_root:
            in_hot = len(b["path"]) > 1 and b["path"][1] == hot_root
            if in_hot and not rec.get("hot_since"):
                rec["hot_since"] = today      # first sync that sees it there
            elif not in_hot:
                rec.pop("hot_since", None)
        # With hot_root unset we know nothing about staging, so leave existing
        # stamps alone: a transient config edit must not reset 180 days of TTL.

        rec.update({
            "path": b["path"], "title": b["title"], "url": b["url"],
            "root": b["root"], "parent_guid": b["parent_guid"],
            "added": iso(b["added"]), "used": iso(b["used"]),
            "age_days": days_ago(b["added"]),
            "cold": bool(not b["used"] and (days_ago(b["added"]) or 0) > cold_days),
        })
        rec.pop("missing_since", None)

    for guid in gone:
        if prune:
            recs.pop(guid)
        else:
            recs[guid].setdefault("missing_since", today)
    return new, gone, moved, stale


# ---------------------------------------------------------------- commands

def cmd_stats(args):
    data, path = load_tree()
    bms = list(bookmarks(data))
    fls = list(folders(data))
    recs = read_index()

    th = thresholds()
    depth = {}
    for b in bms:
        depth[len(b["path"]) - 1] = depth.get(len(b["path"]) - 1, 0) + 1
    deep = sum(v for k, v in depth.items() if k >= th["deep_level"])
    thin = [f for f in fls if is_thin(f, th)]
    fat = [f for f in fls if f["n_urls"] >= th["fat_folder_min"]]
    cold = [b for b in bms
            if not b["used"] and (days_ago(b["added"]) or 0) > th["cold_days"]]

    print(f"file            {path}")
    print(f"modified        {datetime.fromtimestamp(os.path.getmtime(path)):%Y-%m-%d %H:%M}")
    print(f"bookmarks       {len(bms)}")
    print(f"folders         {len(fls)}")
    print(f"indexed         {len(recs)}  (unindexed: {len([b for b in bms if b['guid'] not in recs])})")
    print()
    print("HEALTH")
    print(f"  avg depth                    {sum(len(b['path']) - 1 for b in bms) / max(1, len(bms)):.2f}")
    print(f"  depth histogram              {dict(sorted(depth.items()))}")
    print(f"  bookmarks {th['deep_level']}+ deep             {deep}")
    print(f"  thin folders (<={th['thin_folder_max']})           {len(thin)} holding {sum(f['n_urls'] for f in thin)}")
    print(f"  fat folders (>={th['fat_folder_min']})           {len(fat)}")
    print(f"  never opened + {th['cold_days']}d+       {len(cold)}")
    print()
    print("ROOTS")
    for root in ROOTS:
        top = [f for f in fls if f["root"] == root and len(f["path"]) == 2]
        n = len([b for b in bms if b["root"] == root])
        if n or top:
            print(f"  {root:14} {n:5} bookmarks, {len(top)} top folders")
            for f in sorted(top, key=lambda x: x["path"]):
                inside = len([b for b in bms if b["path"][:2] == f["path"]])
                print(f"      {f['name']:<28} {inside:5}")


def cmd_profile_scan(args):
    """Evidence pack for the setup interview: what the tree reveals about its owner.

    Prints observations, never conclusions. Each block is something to ask about.
    """
    data, _ = load_tree()
    bms = list(bookmarks(data))
    fls = list(folders(data))
    th = thresholds()

    def scripts_of(s):
        """Which writing systems a string uses — not everyone writes Latin+Cyrillic."""
        found = set()
        for ch in s:
            if ch.isalpha():
                try:
                    found.add(unicodedata.name(ch).split()[0])
                except ValueError:
                    pass
        return found

    print("## roots and their top folders (in the order Chrome shows them)")
    for root in ROOTS:
        top = [c for c in (data["roots"].get(root) or {}).get("children", [])]
        n = len([b for b in bms if b["root"] == root])
        if not top and not n:
            continue
        print(f"\n{root}: {n} bookmarks")
        names = [c.get("name", "") for c in top if c.get("type") != "url"]
        for c in top:
            if c.get("type") == "url":
                continue
            inside = len([b for b in bms if len(b["path"]) > 1
                          and b["root"] == root and b["path"][1] == c.get("name")])
            kids = c.get("children", [])
            sub = sum(1 for k in kids if k.get("type") != "url")
            print(f"  {c.get('name'):<24} {inside:5} bookmarks, {sub} subfolders, "
                  f"name {len(c.get('name',''))} chars")
        if names:
            print(f"  -> alphabetical: {names == sorted(names)}   "
                  f"longest name: {max(len(n) for n in names)} chars")
        bare = [c for c in top if c.get("type") == "url"]
        if bare:
            print(f"  -> {len(bare)} bare links sitting at root level, names: "
                  f"{[c.get('name') for c in bare]}")
            print("     (very short names usually mean a quick-launch row, not taxonomy)")

    print("\n## subfolder names reused across unrelated branches")
    reuse = {}
    for f in fls:
        if len(f["path"]) > 2:
            reuse.setdefault(f["name"], set()).add(f["path"][1])
    common = sorted(((n, sorted(r)) for n, r in reuse.items() if len(r) > 1),
                    key=lambda x: (-len(x[1]), x[0]))[:25]
    for name, branches in common:
        print(f"  {name:<22} under {len(branches)}: {', '.join(branches)}")
    print("  (a repeated vocabulary is a content-type layer beneath the topic layer)")

    print("\n## writing systems used in folder names")
    for root in sorted({f["path"][1] for f in fls if len(f["path"]) == 2}):
        sub = [f["name"] for f in fls if len(f["path"]) > 2 and f["path"][1] == root]
        if not sub:
            continue
        tally = {}
        for name in sub:
            for script in scripts_of(name):
                tally[script] = tally.get(script, 0) + 1
        if len(tally) > 1:
            parts = ", ".join(f"{k.lower()} {v}" for k, v in
                              sorted(tally.items(), key=lambda x: -x[1]))
            print(f"  {root:<20} {len(sub)} folders — {parts}")
    print("  (a split that follows topic rather than chance is a rule to preserve)")

    print("\n## folders that look like staging or archive")
    for f in fls:
        if re.search(r"archive|inbox|read.?later|temp|unsorted|to.?do|разобрать|архив",
                     f["name"], re.I):
            total = len([b for b in bms if b["path"][:len(f["path"])] == f["path"]])
            print(f"  {pathstr(f['path'])}  ({total} bookmarks including subfolders)")

    print("\n## health at current thresholds")
    thin = [f for f in fls if is_thin(f, th)]
    deep = [b for b in bms if len(b["path"]) - 1 >= th["deep_level"]]
    cold = [b for b in bms if not b["used"]
            and (days_ago(b["added"]) or 0) > th["cold_days"]]
    print(f"  thresholds in effect: {json.dumps(th)}")
    print(f"  thin folders {len(thin)}, {th['deep_level']}+ deep {len(deep)}, "
          f"cold {len(cold)}, total {len(bms)} in {len(fls)} folders")
    dates = sorted(b["added"] for b in bms if b["added"])
    if dates:
        years = {}
        for d in dates:
            y = datetime.fromtimestamp(d).year
            years[y] = years.get(y, 0) + 1
        print(f"  collected {iso(dates[0])} .. {iso(dates[-1])}, per year: {years}")


def cmd_tree(args):
    data, _ = load_tree()
    bms = list(bookmarks(data))
    for f in folders(data):
        if len(f["path"]) - 1 > args.depth:
            continue
        inside = len([b for b in bms if b["path"][:len(f["path"])] == f["path"]])
        indent = "  " * (len(f["path"]) - 1)
        flag = "  ← thin" if is_thin(f) else ""
        print(f"{indent}{f['name'] or f['root']}/  [{inside}]{flag}\t{f['guid']}")


def cmd_folder(args):
    """Everything under a path fragment or parent guid — folders first, so the
    guid needed as a patch target is right here rather than a `tree` away."""
    data, _ = load_tree()
    recs = read_index()
    target = args.target
    print("# kind\tguid\tpath\ttitle\turl\tadded\tused\tlink\ttags")
    for f in folders(data):
        p = pathstr(f["path"])
        if target not in p and target != f["guid"] and target != f["parent_guid"]:
            continue
        print("\t".join(["folder", f["guid"], p, f["name"], "", "", "", "",
                         f"{f['n_urls']} bookmarks, {f['n_folders']} subfolders"]))
    for b in bookmarks(data):
        p = pathstr(b["path"])
        if target not in p and target != b["parent_guid"]:
            continue
        rec = recs.get(b["guid"], {})
        print("\t".join(["url", b["guid"], p, b["title"], b["url"],
                         iso(b["added"]), iso(b["used"]) or "-",
                         rec.get("link", "?"), ",".join(rec.get("tags", []))]))


def cmd_sync(args):
    data, _ = load_tree()
    recs = read_index()
    before = len(recs)
    live_guids = {b["guid"] for b in bookmarks(data)}   # one walk, not one per record
    live = len(live_guids)

    # A sync that would erase most of the index is almost always pointing at the
    # wrong profile, or running before Chrome sync has pulled the tree down.
    if before and not args.prune:
        share = len([g for g in recs if g not in live_guids])
        if share > max(20, before * 0.05):
            print(f"refusing to sync: {share} of {before} indexed bookmarks are "
                  f"missing from Chrome ({live} present).", file=sys.stderr)
            print(f"  bookmarks file: {bookmarks_path()}", file=sys.stderr)
            print("  If that path and profile are right and you really deleted them, "
                  "re-run with --prune.", file=sys.stderr)
            sys.exit(2)

    new, gone, moved, stale = sync_records(data, recs, prune=args.prune)
    write_index(recs)
    build_db(recs)
    print(f"indexed={len(recs)} new={len(new)} missing={len(gone)} "
          f"moved={len(moved)} re-queued={len(stale)}"
          + (" (pruned)" if args.prune else ""))
    if gone and not args.prune:
        print(f"  {len(gone)} records kept but hidden from search; "
              f"use --prune to drop them for good")
    if new and args.verbose:
        for guid in new:
            print("NEW\t" + guid)


def cmd_dump(args):
    """Emit bookmarks that need enrichment, as TSV for the model.

    This is a QUEUE, not a page: already-enriched records are excluded, so each
    call returns the next slice of remaining work and `--offset` would skip real
    bookmarks. Repeat `dump --limit N` / `ingest` until it comes back empty.
    """
    data, _ = load_tree()
    recs = read_index()
    live = list(bookmarks(data))
    if args.all:
        todo = live[args.offset:]
    else:
        if args.offset:
            die("dump is a queue, not a page: already-enriched records are excluded "
                "automatically, so --offset would skip bookmarks that still need "
                "tags. Just repeat `dump --limit N` until it returns nothing. "
                "(--offset is only meaningful together with --all.)")
        todo = [b for b in live
                if b["guid"] not in recs or not recs[b["guid"]].get("tags")]
    remaining = len(todo)
    if args.limit:
        todo = todo[:args.limit]
    left = remaining - len(todo)
    print(f"# {len(todo)} bookmarks in this batch, {left} "
          + ("remaining in this pass" if args.all else "still queued after it"))
    print("# guid\tpath\ttitle\turl")
    for b in todo:
        print("\t".join([b["guid"], pathstr(b["path"]), b["title"], b["url"]]))


def cmd_ingest(args):
    """Merge model-produced JSONL enrichment into the index."""
    recs = read_index()
    data, _ = load_tree()
    live = {b["guid"]: b for b in bookmarks(data)}
    added = 0
    src = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")
    for line in src:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        inc = json.loads(line)
        guid = inc.get("guid")
        if guid not in live:
            print(f"skip (not in Chrome): {guid}", file=sys.stderr)
            continue
        rec = recs.setdefault(guid, {"guid": guid})
        # `lang` and `para` were dropped: nothing read them. Retention policy comes
        # from the root folder's role in profile.md, not from a per-bookmark field.
        for key in ("tags", "summary", "kind", "evergreen", "obsolete", "googlable"):
            if key in inc:
                rec[key] = inc[key]
        added += 1
    if src is not sys.stdin:
        src.close()
    sync_records(data, recs)
    write_index(recs)
    build_db(recs)
    print(f"ingested={added} indexed={len(recs)}")


def _fts_query(terms, phrase=False):
    """OR of prefix matches, with a crude stem for inflected languages.

    FTS5's unicode61 tokenizer does not stem. Prefix matching covers English
    plurals by accident ("queue"* matches queues) but not suffixal inflection:
    "блокировки"* would miss a document containing "блокировка". Emitting a
    shortened prefix alongside the literal term costs nothing and fixes it.

    A quoted multi-word argument is split into separate terms rather than
    becoming an exact phrase: quoting is what people do to group words, and
    silently turning that into a phrase match returns zero for no visible reason.
    Use --phrase when an exact sequence is genuinely wanted.
    """
    if phrase:
        joined = " ".join(re.sub(r'["*]', " ", t).strip() for t in terms).strip()
        return f'"{joined}"' if joined else ""
    words = []
    for term in terms:
        words.extend(re.sub(r'["*]', " ", term).split())
    parts = []
    for term in words:
        term = term.strip()
        if not term:
            continue
        parts.append(f'"{term}"*')
        if len(term) > 5 and not term.isascii():
            stem = term[:-2]
            if len(stem) >= 4:
                parts.append(f'"{stem}"*')
    seen, unique = set(), []
    for part in parts:
        if part not in seen:
            seen.add(part)
            unique.append(part)
    return " OR ".join(unique)


def cmd_search(args):
    recs = read_index()
    if not recs:
        die("no index; run: bm.py sync")
    if db_is_stale():
        # Cheap and pure — a pulled index.jsonl would otherwise be invisible here.
        print("# index.db was stale, rebuilt from index.jsonl", file=sys.stderr)
        build_db(recs)

    data, _ = load_tree()
    live = {b["guid"] for b in bookmarks(data)}
    missing = len(live - set(recs))
    unenriched = len([g for g in live & set(recs) if not recs[g].get("tags")])

    con = sqlite3.connect(DB)
    q = _fts_query(args.terms, phrase=args.phrase)
    if not q:
        die("empty query")
    where = "WHERE bm MATCH ?"
    params = [q]
    if args.root:
        where += " AND m.root = ?"
        params.append(args.root)
    total = con.execute(
        f"SELECT COUNT(*) FROM bm JOIN meta m ON m.guid = bm.guid {where}",
        params).fetchone()[0]
    rows = con.execute(f"""
        SELECT m.guid, m.parent_guid, m.path, m.title, m.url, m.kind, m.summary,
               m.added, m.used, m.cold, m.link, bm.tags,
               bm25(bm, 0.0, 2.0, 3.0, 1.0, 3.0, 2.0) AS rank
        FROM bm JOIN meta m ON m.guid = bm.guid {where}
        ORDER BY rank LIMIT ?""", params + [args.n]).fetchall()
    con.close()

    indexed = len(live & set(recs))
    print(f"# query={q!r} matches={total} shown={len(rows)} missing={missing} "
          f"unenriched={unenriched}/{indexed}")
    if indexed and unenriched > indexed * 0.5:
        print("# NOTE: most records have no tags, so this is keyword matching, not "
              "semantic search. Paraphrases and cross-language queries will miss. "
              "Run the enrichment pass (see references/index.md).")
    if missing:
        print(f"# NOTE: {missing} bookmarks in Chrome are not indexed — run sync.")
    if total < 5:  # true match count, not the -n-capped `shown`
        print("# NOTE: few or no hits. Do NOT report a miss yet — re-run with a "
              "different vocabulary (other language, brand name vs function, "
              "colloquial vs technical). See the Find mode in SKILL.md.")
    print("# guid\tparent_guid\tpath\ttitle\turl\tkind\tsummary\tadded\tused\t"
          "cold\tlink\ttags\tscore")
    for r in rows:
        row = list(r)
        row[4] = row[4][:110] + ("…" if len(row[4]) > 110 else "")  # url
        print("\t".join(str(x) for x in row))


def _request(url, timeout, method):
    """(status_or_error, dns_failed)."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, False
    except urllib.error.HTTPError as exc:
        return exc.code, False
    except urllib.error.URLError as exc:
        # The interesting failure hides in .reason, not in the exception type.
        reason = exc.reason
        dns = isinstance(reason, socket.gaierror) or "Name or service not known" \
            in str(reason) or "nodename nor servname" in str(reason)
        return f"err:{type(reason).__name__ if isinstance(reason, Exception) else reason}", dns
    except Exception as exc:
        return f"err:{type(exc).__name__}", False


def _check(url, timeout):
    """Returns (verdict, detail). Many servers answer HEAD with 404 while the page
    is fine, so anything that is not a clean HEAD success is retried with GET."""
    head, dns = _request(url, timeout, "HEAD")
    if dns:
        return "dead", f"HEAD dns-failure"
    if isinstance(head, int) and 200 <= head < 400:
        return "ok", f"HEAD {head}"

    # A server that needs the GET retry is often a slow one, and under 16 workers
    # it is the first to time out. Give the deciding request more room.
    get, dns = _request(url, timeout * 2, "GET")
    if dns:
        return "dead", "GET dns-failure"
    if isinstance(get, int):
        if 200 <= get < 400:
            return "ok", f"HEAD {head} / GET {get}"
        if get in (404, 410):
            return "dead", f"HEAD {head} / GET {get}"
        return "suspect", f"HEAD {head} / GET {get}"
    return "suspect", f"HEAD {head} / GET {get}"


def cmd_check_links(args):
    recs = read_index()
    data, _ = load_tree()
    sync_records(data, recs)
    todo = []
    for guid, rec in recs.items():
        if not rec.get("url", "").lower().startswith(("http://", "https://")):
            continue  # never fetch file:, javascript:, chrome: and friends
        if rec.get("missing_since"):
            continue
        if args.cold and not rec.get("cold"):
            continue
        if rec.get("checked") and not args.recheck:
            continue
        todo.append(guid)
    if args.limit:
        todo = todo[:args.limit]
    # DNS is the one failure that breaks identically for every URL at once —
    # captive-portal wifi, a half-connected VPN, a resolver outage. Without this
    # check the whole collection lands in the "dead, safe to delete" bucket.
    canaries = ["github.com", "google.com", "cloudflare.com"]
    reachable = []
    for host in canaries:
        try:
            socket.getaddrinfo(host, 443)
            reachable.append(host)
        except OSError:
            pass
    if not reachable:
        die("DNS is not resolving on this machine (tried " + ", ".join(canaries) +
            "). Every URL would be reported dead. Fix the network and re-run.")

    print(f"checking {len(todo)} urls with {args.workers} workers", file=sys.stderr)

    results, done, dns_failures = {}, 0, 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_check, recs[g]["url"], args.timeout): g for g in todo}
        for fut in cf.as_completed(futs):
            guid = futs[fut]
            verdict, detail = fut.result()
            results[guid] = (verdict, detail)
            if "dns-failure" in detail:
                dns_failures += 1
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(todo)}", file=sys.stderr)

    # A partial network fault looks like mass death. But an old collection really
    # does contain dead domains, and on a small batch a percentage means nothing —
    # so only a large batch failing at a rate no real collection reaches is refused.
    dns_limit = 0.4
    if (len(todo) >= 50 and dns_failures > len(todo) * dns_limit
            and not args.accept_dns_failures):
        die(f"discarding this run: {dns_failures} of {len(todo)} urls failed DNS "
            f"({dns_failures * 100 // len(todo)}%). A collection does not lose that "
            f"share of its domains at once — this looks like a partial network or "
            f"resolver fault. Nothing was written.\n"
            f"  If you are certain the network is healthy, re-run with "
            f"--accept-dns-failures.")

    today = datetime.now().strftime("%Y-%m-%d")
    for guid, (verdict, detail) in results.items():
        recs[guid]["link"] = verdict
        recs[guid]["link_status"] = detail
        recs[guid]["checked"] = today
    write_index(recs)
    build_db(recs)
    tally = {}
    for rec in recs.values():
        tally[rec.get("link", "unchecked")] = tally.get(rec.get("link", "unchecked"), 0) + 1
    print(json.dumps(tally, indent=2))

    # A sweep is only useful once someone can act on it, so hand over the browsable
    # report rather than leaving 300 verdicts sitting in a JSONL file.
    if not args.no_report:
        path, total, checked = write_html_report()
        print(f"\nreport: {path}  ({total} bookmarks, {checked} links checked)")
        print("open it, decide, then build a patch with the guids it lists")


REPORT_CSS = """
 :root { color-scheme: light dark;
   --bg:#fbfaf8; --fg:#1a1a1a; --mut:#6b6660; --line:#e2ded8; --card:#fff;
   --ev:#0d7a5f; --evb:#dff3ec; --ob:#9a5b00; --obb:#fdefd8; --gg:#5a5f8a; --ggb:#e9eaf5;
   --acc:#b03030; --accb:#fbeaea; }
 @media (prefers-color-scheme: dark) { :root {
   --bg:#141311; --fg:#eceae6; --mut:#94908a; --line:#2c2a27; --card:#1c1b19;
   --ev:#5cd6b0; --evb:#12332a; --ob:#e0a44e; --obb:#3a2a10; --gg:#a8adda; --ggb:#22243a;
   --acc:#ff8a8a; --accb:#37191a; } }
 * { box-sizing:border-box }
 body { margin:0 0 76px; background:var(--bg); color:var(--fg);
   font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
 header { padding:32px 28px 20px; border-bottom:1px solid var(--line); }
 h1 { margin:0 0 6px; font-size:26px; letter-spacing:-.02em; }
 .meta { color:var(--mut); font-size:13px; }
 nav { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:6px;
   padding:12px 28px; background:var(--bg); border-bottom:1px solid var(--line); }
 nav a { color:var(--fg); text-decoration:none; font-size:13px; padding:5px 11px;
   border:1px solid var(--line); border-radius:99px; background:var(--card); }
 nav a:hover { border-color:var(--mut); }
 nav a b { color:var(--mut); font-weight:600; margin-left:3px; }
 section { padding:30px 28px; border-bottom:1px solid var(--line); }
 .head { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }
 h2 { font-size:19px; margin:0 0 6px; letter-spacing:-.01em; }
 h2 .n { color:var(--mut); font-weight:400; }
 .picked { color:var(--acc); font-weight:500; font-size:14px; }
 .all { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--mut);
   border:1px solid var(--line); background:var(--card); padding:5px 11px;
   border-radius:99px; cursor:pointer; white-space:nowrap; }
 .all:hover { border-color:var(--acc); color:var(--acc); }
 .blurb { margin:0 0 4px; color:var(--mut); max-width:70ch; font-size:14px; }
 .where { margin:0 0 16px; color:var(--mut); font-size:12px; max-width:110ch; }
 .tw { overflow-x:auto; }
 table { width:100%; border-collapse:collapse; font-size:13.5px; }
 th { text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.06em;
   color:var(--mut); font-weight:600; padding:0 12px 8px 0; border-bottom:1px solid var(--line);
   cursor:pointer; user-select:none; white-space:nowrap; }
 th:hover { color:var(--fg); }
 th::after { content:"\\2195"; opacity:.28; margin-left:5px; font-size:10px; }
 th.asc::after { content:"\\2191"; opacity:1; }
 th.desc::after { content:"\\2193"; opacity:1; }
 th.nosort { cursor:default; width:34px; }
 th.nosort::after { content:""; }
 td { padding:9px 12px 9px 0; border-bottom:1px solid var(--line); vertical-align:top; }
 tr:hover td { background:var(--card); }
 td.c { width:34px; padding-top:11px; }
 input[type=checkbox] { width:15px; height:15px; accent-color:var(--acc); cursor:pointer; }
 tr.marked td { background:var(--accb); }
 tr.marked .t a { color:var(--acc); text-decoration:line-through; }
 tr.marked .s, tr.marked .p { opacity:.55; }
 .t { max-width:46ch; }
 .t a { color:var(--fg); text-decoration:none; border-bottom:1px solid var(--line); }
 .t a:hover { border-color:currentColor; }
 .s { color:var(--mut); font-size:12px; margin-top:2px; }
 .p, .st, .d { color:var(--mut); font-size:12px; white-space:nowrap; }
 .g { color:var(--mut); font-size:10.5px; font-family:ui-monospace,SFMono-Regular,monospace; }
 .b { display:inline-block; font-size:10px; padding:1px 6px; border-radius:99px;
   margin-left:6px; vertical-align:1px; white-space:nowrap; }
 .ev { color:var(--ev); background:var(--evb); }
 .ob { color:var(--ob); background:var(--obb); }
 .gg { color:var(--gg); background:var(--ggb); }
 footer { padding:24px 28px; color:var(--mut); font-size:12.5px; max-width:80ch; }
 #bar { position:fixed; left:0; right:0; bottom:0; z-index:20; display:flex;
   align-items:center; gap:12px; padding:13px 28px; background:var(--card);
   border-top:1px solid var(--line); box-shadow:0 -6px 22px rgba(0,0,0,.09);
   transform:translateY(105%); transition:transform .18s ease; flex-wrap:wrap; }
 #bar.on { transform:none; }
 #bar .cnt { font-weight:600; }
 #bar .cnt b { color:var(--acc); font-size:17px; }
 #bar button { font:inherit; font-size:13px; padding:7px 14px; border-radius:8px;
   border:1px solid var(--line); background:var(--bg); color:var(--fg); cursor:pointer; }
 #bar button:hover { border-color:var(--mut); }
 #bar button.pri { background:var(--acc); border-color:var(--acc); color:#fff; }
 @media (prefers-color-scheme: dark) { #bar button.pri { color:#1a1a1a; } }
 #bar .sp { flex:1 }
 #bar .hint { color:var(--mut); font-size:12px; }
"""

REPORT_JS = r"""
var KEY = 'bm-cleanup-marks';
var marks = new Set(JSON.parse(localStorage.getItem(KEY) || '[]'));

function save() { localStorage.setItem(KEY, JSON.stringify(Array.from(marks))); }
function paintRow(cb) { cb.closest('tr').classList.toggle('marked', cb.checked); }

function refresh() {
  document.querySelectorAll('section[data-cat]').forEach(function (sec) {
    var boxes = sec.querySelectorAll('.pick');
    var on = sec.querySelectorAll('.pick:checked').length;
    var all = sec.querySelector('.allbox');
    if (all) {
      all.checked = on > 0 && on === boxes.length;
      all.indeterminate = on > 0 && on < boxes.length;
    }
    var tag = sec.querySelector('.picked');
    if (tag) { tag.hidden = on === 0; tag.querySelector('b').textContent = on; }
  });
  document.getElementById('bar').classList.toggle('on', marks.size > 0);
  document.getElementById('cnt').textContent = marks.size;
  save();
}

document.querySelectorAll('.pick').forEach(function (cb) {
  if (marks.has(cb.dataset.guid)) cb.checked = true;
  paintRow(cb);
  cb.addEventListener('change', function () {
    if (cb.checked) marks.add(cb.dataset.guid); else marks.delete(cb.dataset.guid);
    paintRow(cb); refresh();
  });
});

document.querySelectorAll('.allbox').forEach(function (all) {
  all.addEventListener('change', function () {
    all.closest('section').querySelectorAll('.pick').forEach(function (cb) {
      if (cb.checked === all.checked) return;
      cb.checked = all.checked;
      if (cb.checked) marks.add(cb.dataset.guid); else marks.delete(cb.dataset.guid);
      paintRow(cb);
    });
    refresh();
  });
});

document.querySelectorAll('table').forEach(function (table) {
  table.querySelectorAll('th').forEach(function (th, col) {
    if (th.classList.contains('nosort')) return;
    th.addEventListener('click', function () {
      var body = table.tBodies[0];
      var desc = !th.classList.contains('desc');
      table.querySelectorAll('th').forEach(function (o) { o.classList.remove('asc','desc'); });
      th.classList.add(desc ? 'desc' : 'asc');
      var rs = Array.prototype.slice.call(body.rows);
      rs.sort(function (a, b) {
        var x = a.cells[col], y = b.cells[col];
        x = (x.dataset.v !== undefined ? x.dataset.v : x.textContent).trim();
        y = (y.dataset.v !== undefined ? y.dataset.v : y.textContent).trim();
        var n = x.localeCompare(y, 'ru', {numeric: true});
        return desc ? -n : n;
      });
      rs.forEach(function (r) { body.appendChild(r); });
    });
  });
});

// The patch must be reviewable by whoever applies it, not just machine-valid:
// title, path and category travel with each op so a wrong selection is visible
// before the write. bm.py's apply reads only op/guid and ignores the rest.
function buildPatch() {
  var ops = [];
  marks.forEach(function (g) {
    var tr = document.querySelector('tr[data-guid="' + g + '"]');
    var op = {op: 'delete', guid: g};
    if (tr) {
      op.title = tr.querySelector('.t a').textContent.trim();
      op.path = tr.querySelector('.p').textContent.trim();
      op.category = tr.closest('section').querySelector('h2').firstChild.textContent.trim();
    }
    ops.push(op);
  });
  ops.sort(function (a, b) { return (a.path || '').localeCompare(b.path || '', 'ru'); });
  return {
    generated: new Date().toISOString().slice(0, 16).replace('T', ' '),
    source: 'bookmarks-cleanup report',
    count: ops.length,
    ops: ops
  };
}

document.getElementById('only').addEventListener('click', function () {
  var on = document.body.classList.toggle('onlymarked');
  this.textContent = on ? 'Показать все' : 'Только отмеченные';
  document.querySelectorAll('tr[data-guid]').forEach(function (tr) {
    tr.style.display = (on && !tr.classList.contains('marked')) ? 'none' : '';
  });
});

document.getElementById('clear').addEventListener('click', function () {
  if (!confirm('Снять все ' + marks.size + ' отметок?')) return;
  marks.clear();
  document.querySelectorAll('.pick').forEach(function (cb) { cb.checked = false; paintRow(cb); });
  refresh();
});

document.getElementById('patch').addEventListener('click', function () {
  var blob = new Blob([JSON.stringify(buildPatch(), null, 2)], {type: 'application/json'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bookmarks-delete-patch.json';
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById('copy').addEventListener('click', function () {
  var self = this;
  navigator.clipboard.writeText(JSON.stringify(buildPatch(), null, 2)).then(function () {
    self.textContent = 'Скопировано';
    setTimeout(function () { self.textContent = 'Скопировать патч'; }, 1400);
  });
});

refresh();
"""


def report_categories(recs):
    """(anchor, title, explanation, items) — the same grouping cmd_report prints,
    ordered by how safe each group is to act on."""
    dead = [r for r in recs if r.get("link") == "dead"]
    return [
        ("safest", "Мёртвые и устаревшие",
         "Два независимых сигнала совпали: ссылка не отвечает и технология мертва. "
         "Самая безопасная группа — удалять можно пачкой.",
         [r for r in dead if r.get("obsolete") and not r.get("evergreen")]),
        ("evergreen", "Мёртвые, но вечнозелёные",
         "Ссылка умерла, ценность содержимого — нет. Грамматика, шпаргалки, основы. "
         "Здесь правильнее найти замену, чем удалить.",
         [r for r in dead if r.get("evergreen")]),
        ("dead-rest", "Мёртвые, остальные",
         "404, 410 или домен не резолвится, подтверждено GET-запросом после HEAD. "
         "Разбирать по веткам.",
         [r for r in dead if not r.get("obsolete") and not r.get("evergreen")]),
        ("obsolete-alive", "Устаревшие, но ссылка живая",
         "Страница открывается, но технология или повод устарели: мёртвый стек, "
         "старые вакансии, снятые с продажи товары.",
         [r for r in recs if r.get("obsolete") and r.get("link") != "dead"]),
        ("suspect", "Подозрительные — проверить руками",
         "403, 429, таймауты, битые сертификаты. Чаще всего живы и просто отшивают "
         "ботов. На удаление не предлагаются никогда.",
         [r for r in recs if r.get("link") == "suspect"]),
        ("googlable", "Тривиально гуглится",
         "Главные страницы известных инструментов — найдутся одним запросом. "
         "Ценность закладки низкая, но проверь вечнозелёные.",
         [r for r in recs if r.get("googlable") and not r.get("evergreen")
          and r.get("link") != "dead"]),
    ]


def write_html_report(path=None):
    """Browsable cleanup report: clickable titles, folder paths, guids for patches."""
    import html as _html

    path = os.path.expanduser(
        path or config().get("report_path", "~/bookmarks-cleanup.html"))
    recs = [r for r in read_index().values() if not r.get("missing_since")]
    data, _ = load_tree()
    th = thresholds()
    thin = [f for f in folders(data) if is_thin(f, th)]

    def esc(s):
        return _html.escape(str(s or ""))

    def path_of(r):
        return " › ".join(r.get("path", [])[1:])

    def rows(items):
        out = []
        for r in sorted(items, key=lambda x: (path_of(x), x.get("title", ""))):
            badges = ""
            if r.get("evergreen"):
                badges += '<span class="b ev">вечнозелёная</span>'
            if r.get("obsolete"):
                badges += '<span class="b ob">устарело</span>'
            if r.get("googlable"):
                badges += '<span class="b gg">гуглится</span>'
            guid = esc(r.get("guid"))
            out.append(
                f'<tr data-guid="{guid}">'
                f'<td class="c"><input type="checkbox" class="pick" data-guid="{guid}"></td>'
                f'<td class="t"><a href="{esc(r.get("url"))}" target="_blank" '
                f'rel="noopener">{esc(r.get("title") or r.get("url"))[:110]}</a>{badges}'
                f'<div class="s">{esc(r.get("summary", ""))}</div></td>'
                f'<td class="p">{esc(path_of(r))}</td>'
                f'<td class="st">{esc(r.get("link_status", ""))}</td>'
                # empty dates sort last in both directions rather than clumping at the top
                f'<td class="d" data-v="{esc(r.get("added") or "0000-00-00")}">'
                f'{esc(r.get("added", ""))}</td></tr>')
        return "\n".join(out)

    def where(items, n=8):
        c = {}
        for r in items:
            b = " › ".join(r.get("path", [])[1:3])
            c[b] = c.get(b, 0) + 1
        top = sorted(c.items(), key=lambda x: -x[1])[:n]
        return " · ".join(f"{esc(b)} ({k})" for b, k in top)

    cats = [(cid, name, blurb, items)
            for cid, name, blurb, items in report_categories(recs) if items]

    nav = "".join(f'<a href="#{cid}">{esc(name)} <b>{len(items)}</b></a>'
                  for cid, name, _, items in cats)
    nav += f'<a href="#thin">Тонкие папки <b>{len(thin)}</b></a>'

    sections = []
    for cid, name, blurb, items in cats:
        sections.append(
            f'<section id="{cid}" data-cat="{cid}"><div class="head">'
            f'<label class="all"><input type="checkbox" class="allbox">'
            f'<span>отметить группу</span></label>'
            f'<h2>{esc(name)} <span class="n">{len(items)}</span>'
            f'<span class="picked" hidden>· отмечено <b>0</b></span></h2></div>'
            f'<p class="blurb">{esc(blurb)}</p><p class="where">{where(items)}</p>'
            f'<div class="tw"><table><thead><tr><th class="nosort"></th>'
            f'<th>Закладка</th><th>Папка</th><th>Статус</th><th>Добавлена</th></tr></thead>'
            f'<tbody>{rows(items)}</tbody></table></div></section>')

    thin_rows = "\n".join(
        f'<tr><td class="p">{esc(" › ".join(f["path"][1:]))}</td>'
        f'<td class="st">{f["n_urls"]} закладк{"а" if f["n_urls"] == 1 else "и"}</td>'
        f'<td class="g">{esc(f["guid"])}</td></tr>'
        for f in sorted(thin, key=lambda x: x["path"]))
    sections.append(
        f'<section id="thin"><div class="head"><h2>Тонкие папки '
        f'<span class="n">{len(thin)}</span></h2></div>'
        f'<p class="blurb">Папка держит не больше {th["thin_folder_max"]} закладок и '
        f'не имеет подпапок — лишний клик на пути к содержимому. Схлопывание в '
        f'родителя уменьшает глубину. Отметок тут нет: это не удаление, а '
        f'перестройка.</p>'
        f'<div class="tw"><table><thead><tr><th>Путь</th><th>Содержимое</th>'
        f'<th>guid</th></tr></thead>'
        f'<tbody>{thin_rows}</tbody></table></div></section>')

    checked = len([r for r in recs if r.get("checked")])
    dates = sorted(r["checked"] for r in recs if r.get("checked"))
    span = f"{dates[0]} .. {dates[-1]}" if dates else "не проверялись"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Закладки — кандидаты на уборку</title>
<style>{REPORT_CSS}</style></head><body>
<header><h1>Закладки — кандидаты на уборку</h1>
<div class="meta">{len(recs)} закладок · проверено ссылок {checked} ({esc(span)}) ·
 отчёт от {datetime.now():%Y-%m-%d %H:%M}</div></header>
<nav>{nav}</nav>
{"".join(sections)}
<footer>
<p><b>Как пользоваться.</b> Галочка = «удалить», снятая = «оставить». Чекбокс у
заголовка отмечает всю группу разом. Клик по заголовку столбца сортирует таблицу —
например, по дате добавления, чтобы отделить давно забытое от недавнего. Выбор
сохраняется в браузере, можно закрыть вкладку и вернуться к нему позже.</p>
<p>Когда закончишь — «Скачать патч». Файл ляжет в
<code>~/Downloads/bookmarks-delete-patch.json</code>. В каждой операции есть
заголовок, папка и категория, так что перед применением видно, что именно уйдёт.
Применяется через <code>bm.py apply</code>.</p>
<p><b>Прежде чем удалять.</b> Если у профиля включена синхронизация Chrome,
удаление разъедется по всем устройствам, а локальный бэкап вернёт только эту
машину. Безопасный порядок — поставить синхронизацию на паузу, закрыть Chrome,
применить патч, проверить дерево, включить синхронизацию обратно.</p>
</footer>
<div id="bar">
  <span class="cnt">отмечено на удаление: <b id="cnt">0</b></span>
  <button id="only">Только отмеченные</button>
  <button id="copy">Скопировать патч</button>
  <span class="sp"></span>
  <span class="hint">файл падает в ~/Downloads — скажи, и я его прочитаю</span>
  <button id="clear">Снять всё</button>
  <button id="patch" class="pri">Скачать патч</button>
</div>
<script>{REPORT_JS}</script>
</body></html>""")
    return path, len(recs), checked


def cmd_report(args):
    """Cleanup candidates, grouped. Judgement stays with the model; this is evidence."""
    recs = read_index()
    data, _ = load_tree()
    sync_records(data, recs)

    if args.html is not None:
        path, total, checked = write_html_report(args.html or None)
        print(f"{path}\n  {total} bookmarks, {checked} links checked")
        for _, name, _, items in report_categories(
                [r for r in recs.values() if not r.get("missing_since")]):
            print(f"  {len(items):5}  {name}")
        return
    cfg = config()
    th = thresholds()
    hot_days = th["hot_ttl_days"]
    hot_root = cfg.get("hot_folder")

    def emit(title, rows):
        print(f"\n## {title} ({len(rows)})")
        for rec in rows[:args.limit]:
            print("\t".join([rec["guid"], pathstr(rec.get("path", [])),
                             rec.get("title", "")[:70], rec.get("url", "")[:80],
                             rec.get("added", ""), rec.get("link", "?")]))
        if len(rows) > args.limit:
            print(f"... {len(rows) - args.limit} more")

    # Records whose bookmarks are gone from Chrome stay in the index on purpose,
    # but proposing them again would make every cleanup cycle repeat itself.
    vals = [r for r in recs.values() if not r.get("missing_since")]
    orphans = len(recs) - len(vals)
    if orphans:
        print(f"({orphans} indexed bookmarks are no longer in Chrome and are excluded "
              f"below — `sync --prune` drops them for good)")
    emit("dead links (404/410/no dns) — safe to delete",
         [r for r in vals if r.get("link") == "dead"])
    emit("suspect links (403/429/timeout) — verify by hand",
         [r for r in vals if r.get("link") == "suspect"])
    emit("obsolete stack — flagged during enrichment",
         [r for r in vals if r.get("obsolete") and not r.get("evergreen")])
    emit("trivially re-googlable (site homepages, low bookmark value)",
         [r for r in vals if r.get("googlable") and not r.get("evergreen")])
    if hot_root:
        archive = cfg.get("archive_folder", "Archive")
        today = datetime.now().date()

        def in_hot_since(rec):
            # hot_since is stamped by sync when a bookmark is first seen in the
            # staging root. date_added would answer a different question: how old
            # the link is, not how long it has been waiting here.
            if not rec.get("hot_since"):
                return None
            try:
                seen = datetime.strptime(rec["hot_since"], "%Y-%m-%d").date()
            except ValueError:
                return None
            return (today - seen).days

        candidates = [r for r in vals
                      if len(r.get("path", [])) > 1
                      and r["path"][1] == hot_root
                      and archive not in r["path"][2:]]  # already archived
        stale_hot = [r for r in candidates if (in_hot_since(r) or 0) > hot_days]
        emit(f"in {hot_root} longer than {hot_days} days — permanent home or archive",
             stale_hot)
        stamps = [r["hot_since"] for r in candidates if r.get("hot_since")]
        if candidates:
            since = min(stamps) if stamps else "not yet"
            print(f"   ({len(candidates)} bookmarks in {hot_root}; arrival tracking "
                  f"started {since}, so nothing can look older than that yet)")

    fls = list(folders(data))
    thin = [f for f in fls if is_thin(f, th)]
    print(f"\n## thin folders — collapse into parent ({len(thin)})")
    for f in thin[:args.limit]:
        print(f"{f['guid']}\t{pathstr(f['path'])}\t{f['n_urls']} bookmarks")
    if len(thin) > args.limit:
        print(f"... {len(thin) - args.limit} more")


# ---------------------------------------------------------------- patching

# "Google Chrome for Testing" is deliberately absent: automation tools such as
# agent-browser keep one alive for long stretches, and it does not hold the user's
# Bookmarks file open. Blocking on it would train people to disable the guard.
CHROME_PROCESS_NAMES = (
    "Google Chrome", "Google Chrome Beta", "Google Chrome Canary", "Chromium",
    "chrome", "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
)


def chrome_process_state():
    """(running, explanation). Fails CLOSED — if we cannot tell, assume it runs.

    The explanation names the actual processes, so a false positive is diagnosable
    rather than an invitation to set BM_ALLOW_RUNNING.
    """
    pattern = "|".join(re.escape(n) for n in CHROME_PROCESS_NAMES)
    try:
        out = subprocess.run(["pgrep", "-x", pattern], capture_output=True, text=True)
    except (FileNotFoundError, OSError) as exc:
        return True, f"cannot check ({type(exc).__name__}) — assuming it is"
    if out.returncode == 1:
        return False, "no Chrome process"
    if out.returncode != 0:
        return True, f"pgrep failed (rc={out.returncode}) — assuming it is"

    pids = out.stdout.split()
    detail = ", ".join(pids[:5])
    try:
        ps = subprocess.run(["ps", "-p", ",".join(pids), "-o", "pid=,comm="],
                            capture_output=True, text=True)
        if ps.returncode == 0 and ps.stdout.strip():
            detail = "; ".join(line.strip() for line in ps.stdout.strip().splitlines()[:5])
    except (FileNotFoundError, OSError):
        pass
    return True, f"pid {detail}"


def chrome_running():
    # BM_ALLOW_RUNNING exists so the write path can be exercised against a copy
    # of the file while Chrome is open. Never set it against a live profile.
    if os.environ.get("BM_ALLOW_RUNNING") == "1":
        return False
    return chrome_process_state()[0]


def count_nodes(data):
    return sum(1 for _ in walk(data))


def cfg_int(key, default):
    raw = config().get(key, default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        print(f"warning: config {key}={raw!r} is not a number, using {default}",
              file=sys.stderr)
        return default


def make_backup(path, reason, verify=True):
    """Copy the file aside. With verify=True an unreadable copy is an error —
    a backup nobody can parse is not a backup. With verify=False the copy is
    still made and simply recorded with an unknown node count, which is what
    `restore` needs: the file it is replacing may be exactly the broken one."""
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUPS, f"Bookmarks.{stamp}")
    suffix = 1
    while os.path.exists(dest):
        dest = os.path.join(BACKUPS, f"Bookmarks.{stamp}-{suffix:02d}")
        suffix += 1
    shutil.copy2(path, dest)
    try:
        with open(dest, encoding="utf-8") as fh:
            nodes = count_nodes(json.load(fh))
    except Exception:
        if verify:
            raise
        nodes = None
    with open(dest + ".info", "w", encoding="utf-8") as fh:
        json.dump({"reason": reason, "source": path, "created": stamp,
                   "nodes": nodes}, fh, indent=2)
    return dest, nodes


# Only files this tool created count as snapshots. Chrome's own Bookmarks.bak, or
# anything a user copies in for safekeeping, must not become the target of
# `restore --last` just because its name sorts high.
BACKUP_NAME = re.compile(r"Bookmarks\.(\d{8}-\d{6})(?:-(\d+))?$")


def _backup_sort_key(name):
    # Sorting the collision suffix as text would put -10 before -02.
    match = BACKUP_NAME.fullmatch(name)
    if not match:
        return "", 0
    return match.group(1), int(match.group(2) or 0)


def list_backups():
    if not os.path.isdir(BACKUPS):
        return []
    names = [f for f in os.listdir(BACKUPS) if BACKUP_NAME.fullmatch(f)]
    return sorted(names, key=_backup_sort_key)


def prune_backups():
    """Keep the newest `backup_keep`, never fewer than 5. Old snapshots are the
    only way back after a change is noticed late, so this errs toward keeping."""
    keep = max(5, cfg_int("backup_keep", 30))
    names = list_backups()
    for name in names[:-keep]:
        os.remove(os.path.join(BACKUPS, name))
        info = os.path.join(BACKUPS, name + ".info")
        if os.path.exists(info):
            os.remove(info)
    return len(names[:-keep])


def update_checksum(data):
    """Reproduce BookmarkCodec's MD5.

    Chromium feeds std::string values (id, type, url) as raw UTF-8 bytes but
    std::u16string values (titles) as their UTF-16 code units, so titles must be
    hashed as UTF-16LE. Roots are visited in bookmark_bar, other, synced order.
    """
    md5 = hashlib.md5()

    def upd8(s):
        md5.update(s.encode("utf-8"))

    def upd16(s):
        md5.update(s.encode("utf-16-le"))

    def node(n):
        upd8(str(n.get("id", "")))
        upd16(n.get("name", ""))
        if n.get("type") == "url":
            upd8("url")
            upd8(n.get("url", ""))
        else:
            upd8("folder")
            for child in n.get("children", []):
                node(child)

    for root in ROOTS:
        if data["roots"].get(root):
            node(data["roots"][root])
    data["checksum"] = md5.hexdigest()


def index_nodes(data):
    by_guid = {}
    parents = {}
    for n, _, parent, _ in walk(data):
        by_guid[n.get("guid")] = n
        parents[n.get("guid")] = parent
    return by_guid, parents


def find_folder_by_path(data, path):
    """Resolve a path of folder names starting with a root key.

    Refuses to guess when a segment matches more than one sibling: two folders can
    legitimately share a name, and silently taking the first one lands bookmarks
    in the wrong place with nothing to notice it by.
    """
    node = data["roots"].get(path[0])
    if not node:
        return None
    for name in path[1:]:
        matches = [c for c in node.get("children", [])
                   if c.get("type") != "url" and c.get("name") == name]
        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(
                f"path {path} is ambiguous: {len(matches)} folders named {name!r} "
                f"in {node.get('name') or path[0]!r} — target by guid instead")
        node = matches[0]
    return node


def is_thin(folder, th=None):
    th = th or thresholds()
    return (folder["n_folders"] == 0
            and folder["n_urls"] <= th["thin_folder_max"]
            and len(folder["path"]) > 1)


def count_descendants(node):
    n = 0
    for child in node.get("children", []):
        n += 1 + count_descendants(child)
    return n


def max_id(data):
    ids = [0]
    for n, _, _, _ in walk(data):
        try:
            ids.append(int(n.get("id", 0)))
        except ValueError:
            pass
    return max(ids)


def apply_patch(data, ops):
    """Mutate data in place. Returns (log, expected node-count delta).

    Validates before mutating wherever a bad op could destroy data silently.
    The caller is expected to check the real node delta against the expected one.
    """
    by_guid, parents = index_nodes(data)
    root_guids = {(data["roots"].get(r) or {}).get("guid") for r in ROOTS}
    log = []
    delta = 0
    per_op = []
    next_id = max_id(data) + 1

    def is_ancestor_of(candidate, node_guid):
        """True if `candidate` guid is at or above `node_guid` in the tree."""
        cur = node_guid
        while cur:
            if cur == candidate:
                return True
            cur = parents.get(cur)
        return False

    def detach(guid):
        parent_guid = parents.get(guid)
        parent = by_guid.get(parent_guid) if parent_guid else None
        if parent is None:
            for root in ROOTS:
                rnode = data["roots"].get(root)
                if rnode and any(c.get("guid") == guid for c in rnode.get("children", [])):
                    parent = rnode
                    break
        if parent is None:
            raise KeyError(f"parent of {guid} not found")
        parent["children"] = [c for c in parent["children"] if c.get("guid") != guid]
        parent["date_modified"] = now_wk()
        return parent

    def resolve_target(op):
        if op.get("to_guid"):
            node = by_guid.get(op["to_guid"])
            if node is None:
                raise KeyError(f"target folder {op['to_guid']} not found")
        elif op.get("to_path"):
            node = find_folder_by_path(data, op["to_path"])
            if node is None:
                raise KeyError(f"target path {op['to_path']} not found")
        else:
            raise KeyError("op needs to_guid or to_path")
        if node.get("type") == "url":
            # Chromium ignores `children` on url nodes: anything parked under a
            # bookmark is silently dropped the next time Chrome saves.
            raise ValueError(f"target {node.get('name')!r} is a bookmark, not a folder")
        return node

    def require_node(guid, what):
        node = by_guid.get(guid)
        if node is None:
            raise KeyError(f"{what} {guid} not found")
        if guid in root_guids:
            raise ValueError(f"{what} {guid} is a root folder and cannot be moved, "
                             f"renamed or deleted")
        return node

    for index, op in enumerate(ops):
        try:
            kind = op["op"]
        except (TypeError, KeyError):
            raise ValueError(f"op #{index} has no 'op' field") from None
        delta_before = delta

        if kind == "rename":
            node = require_node(op["guid"], "node")
            log.append(f"rename  {node.get('name')!r} -> {op['title']!r}")
            node["name"] = op["title"]

        elif kind == "move":
            node = require_node(op["guid"], "node")
            dest = resolve_target(op)
            if is_ancestor_of(op["guid"], dest.get("guid")):
                # Detaching then re-appending would build an unreachable cycle:
                # json.dump would not complain and the subtree would vanish.
                raise ValueError(
                    f"move would put {node.get('name')!r} inside itself "
                    f"({dest.get('name')!r} is within it) — this would destroy "
                    f"{count_descendants(node) + 1} nodes")
            if parents.get(op["guid"]) == dest.get("guid"):
                log.append(f"move    {node.get('name')!r} already in "
                           f"{dest.get('name')!r}, skipped")
                continue
            detach(op["guid"])
            dest.setdefault("children", []).append(node)
            dest["date_modified"] = now_wk()
            parents[op["guid"]] = dest.get("guid")
            log.append(f"move    {node.get('name')!r} -> {dest.get('name')}")

        elif kind == "delete":
            node = require_node(op["guid"], "node")
            n_inside = count_descendants(node)
            detach(op["guid"])
            delta -= 1 + n_inside
            log.append(f"delete  {node.get('name')!r}"
                       + (f" (+{n_inside} inside)" if n_inside > 0 else ""))

        elif kind == "mkdir":
            dest = resolve_target(op)
            existing = next((c for c in dest.get("children", [])
                             if c.get("type") != "url" and c.get("name") == op["name"]),
                            None)
            if existing is not None:
                # Reusing beats creating a duplicate the user then has to find.
                op["_created_guid"] = existing.get("guid")
                log.append(f"mkdir   {op['name']!r} already exists in "
                           f"{dest.get('name')}, reusing")
                continue
            node = {
                "children": [], "date_added": now_wk(), "date_modified": now_wk(),
                "guid": str(uuid.uuid4()), "id": str(next_id),
                "name": op["name"], "type": "folder",
            }
            next_id += 1
            dest.setdefault("children", []).append(node)
            by_guid[node["guid"]] = node
            parents[node["guid"]] = dest.get("guid")
            delta += 1
            log.append(f"mkdir   {op['name']!r} in {dest.get('name')}")
            op["_created_guid"] = node["guid"]

        elif kind == "add":
            dest = resolve_target(op)
            if not str(op.get("url", "")).lower().startswith(("http://", "https://")):
                raise ValueError(f"add: refusing non-http url {op.get('url')!r}")
            if not op.get("allow_duplicate"):
                wanted = normalize_url(op["url"])
                for existing, path, _, _ in walk(data):
                    if existing.get("type") == "url" \
                            and normalize_url(existing.get("url", "")) == wanted:
                        same = existing.get("url") == op["url"]
                        raise ValueError(
                            f"already bookmarked as {existing.get('name')!r} in "
                            f"{pathstr(path[:-1])}"
                            + ("" if same else f" (as {existing.get('url')})")
                            + ' — move it instead, or pass "allow_duplicate": true')
            node = {
                "date_added": now_wk(), "date_last_used": "0",
                "guid": str(uuid.uuid4()), "id": str(next_id),
                "name": op["title"], "type": "url", "url": op["url"],
            }
            next_id += 1
            dest.setdefault("children", []).append(node)
            by_guid[node["guid"]] = node
            parents[node["guid"]] = dest.get("guid")
            delta += 1
            log.append(f"add     {op['title']!r} -> {dest.get('name')}")

        elif kind == "reorder":
            node = by_guid.get(op["guid"])
            if node is None:
                raise KeyError(f"folder {op['guid']} not found")
            if node.get("type") == "url":
                raise ValueError(f"cannot reorder {node.get('name')!r}: not a folder")
            order = {g: i for i, g in enumerate(op["order"])}
            node.setdefault("children", []).sort(
                key=lambda c: order.get(c.get("guid"), 10**6))
            log.append(f"reorder {node.get('name')!r}")

        else:
            raise ValueError(f"unknown op: {kind}")

        per_op.append((index, kind, delta - delta_before))

    return log, delta, per_op


def diagnose_mismatch(ops, per_op):
    """Replay the ops one at a time against a fresh tree to name the first one
    whose real effect differed from what it claimed. Error path only."""
    data, _ = load_tree()
    expected_by_index = {i: d for i, _, d in per_op}
    for index in range(len(ops)):
        before = count_nodes(data)
        try:
            apply_patch(data, [ops[index]])
        except Exception as exc:
            return f"op #{index} ({ops[index].get('op')}) failed on replay: {exc}"
        actual = count_nodes(data) - before
        expected = expected_by_index.get(index, 0)
        if actual != expected:
            why = ("most likely it overlaps an earlier op in the same patch"
                   if index > 0 else
                   "the tree does not match what the patch assumed — check for "
                   "duplicate guids")
            return (f"op #{index} ({ops[index].get('op')} "
                    f"{ops[index].get('guid', ops[index].get('name', ''))}) changed "
                    f"{actual:+d} nodes, expected {expected:+d} — {why}")
    return "no single op explains it; the ops interact"


def cmd_apply(args):
    if not os.path.exists(args.patch):
        die(f"patch file not found: {args.patch}\n"
            f"  If it came from the cleanup report, the marks are still in the "
            f"browser — reopen the report and press «Скачать патч» again.")
    try:
        with open(args.patch, encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as exc:
        die(f"{args.patch} is not valid JSON: {exc}")
    ops = payload["ops"] if isinstance(payload, dict) else payload
    if not isinstance(ops, list):
        die("patch must be a list of ops, or an object with an 'ops' list")

    # Editing the file only works for a device-local profile. When Chrome stores
    # bookmarks in the account, the server owns the tree and overwrites any file
    # edit on the next merge — the exact failure that lost an evening. Route writes
    # through the extension instead.
    if account_bookmarks_path() and not args.force_file:
        die("this profile stores bookmarks in your Google account, so editing the "
            "file will be undone by sync.\n"
            "  Apply changes through the extension instead:\n"
            "    1. bm.py bridge         (starts the local relay)\n"
            "    2. load the extension in chrome://extensions if not already\n"
            "    3. bm.py apply-live <patch>\n"
            "  (--force-file overrides, but the change will not stick under sync.)")

    data, path = load_tree()
    before = count_nodes(data)
    try:
        log, expected, per_op = apply_patch(data, ops)
    except (KeyError, ValueError, TypeError) as exc:
        die(f"patch rejected, nothing written: {exc}")

    # Every op has a known effect on the node count. If the tree disagrees, some
    # op did something nobody asked for — refuse rather than write and hope.
    after = count_nodes(data)
    if after - before != expected:
        die(f"integrity check failed: node count moved {before} -> {after} "
            f"({after - before:+d}) but the ops account for {expected:+d}. "
            f"Nothing written.\n  {diagnose_mismatch(ops, per_op)}")

    if args.dry_run:
        print(f"{len(log)} operations (dry run, nothing written)")
        for line in log:
            print("  " + line)
        print(f"\nnodes {before} -> {after} ({after - before:+d}), as expected")
        return

    running, why = chrome_process_state()
    if running and os.environ.get("BM_ALLOW_RUNNING") != "1":
        die(f"Chrome is running ({why}) — quit it first, or the changes will be "
            f"overwritten when Chrome exits.")

    backup, backed_up_nodes = make_backup(path, f"before apply of {len(ops)} ops")

    update_checksum(data)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=3)
    os.replace(tmp, path)

    # Read back what actually landed on disk; roll back if it is not what we meant.
    try:
        with open(path, encoding="utf-8") as fh:
            written = json.load(fh)
        if count_nodes(written) != after:
            raise ValueError(f"file has {count_nodes(written)} nodes, expected {after}")
    except Exception as exc:
        try:
            shutil.copy2(backup, path)
        except Exception as rollback_exc:
            die(f"write verification failed ({exc}) AND the automatic rollback "
                f"failed ({rollback_exc}).\n"
                f"  Restore by hand:  cp '{backup}' '{path}'\n"
                f"  Do not start Chrome before doing so.", code=4)
        die(f"write verification failed ({exc}) — restored from {backup}")

    pruned = prune_backups()
    print(f"applied {len(log)} operations")
    for line in log:
        print("  " + line)
    print(f"\nnodes {before} -> {after} ({after - before:+d}), verified on disk")
    print(f"backup: {backup}  ({backed_up_nodes} nodes)")
    print(f"roll back with: bm.py restore --last")
    print(f"{len(list_backups())} backups kept" + (f", {pruned} pruned" if pruned else ""))


def cmd_restore(args):
    """Restore must work when the current file is unreadable — that is the whole
    point of it. Only the backup being restored is validated; the file being
    replaced is treated as opaque bytes."""
    names = list_backups()
    if args.last or not args.backup:
        if not names:
            die(f"no backups in {BACKUPS}")
        src = os.path.join(BACKUPS, names[-1])
    else:
        src = args.backup
        if not os.path.isabs(src):
            src = os.path.join(BACKUPS, src)
    if not os.path.exists(src):
        die(f"backup not found: {src}\n  available: "
            + (", ".join(names[-5:]) if names else "none"))

    try:
        with open(src, encoding="utf-8") as fh:
            restoring = count_nodes(json.load(fh))
    except Exception as exc:
        die(f"refusing to restore from an unreadable backup: {src}\n  {exc}")

    running, why = chrome_process_state()
    if running and os.environ.get("BM_ALLOW_RUNNING") != "1":
        die(f"Chrome is running ({why}) — quit it first.")

    path = bookmarks_path()
    if not os.path.isdir(os.path.dirname(path)):
        die(f"no such Chrome profile directory: {os.path.dirname(path)}\n"
            f"  check `profile` / `bookmarks_file` in config.json — see bm.py status")
    current = "unreadable"
    try:
        with open(path, encoding="utf-8") as fh:
            current = count_nodes(json.load(fh))
    except Exception:
        pass  # that is very likely why we are here

    safety = None
    if os.path.exists(path):
        # The state being left may turn out to be the good one, so keep it even
        # when it does not parse.
        try:
            safety, _ = make_backup(path, "before restore", verify=False)
        except Exception as exc:
            print(f"warning: could not snapshot the current file ({exc}); "
                  f"restoring anyway", file=sys.stderr)

    shutil.copy2(src, path)
    print(f"restored {path}\n  from {src}\n  nodes {current} -> {restoring}")
    if safety:
        print(f"the pre-restore state was saved to {safety}")
    print("run: bm.py sync   (the index still describes the tree you just undid)")


def cmd_backups(args):
    names = list_backups()
    if not names:
        print(f"no backups in {BACKUPS}")
        return
    for name in names:
        info_path = os.path.join(BACKUPS, name + ".info")
        info = {}
        if os.path.exists(info_path):
            with open(info_path, encoding="utf-8") as fh:
                info = json.load(fh)
        size = os.path.getsize(os.path.join(BACKUPS, name))
        nodes = info.get("nodes") or "unverified"
        print(f"{name}\t{nodes} nodes\t{max(1, size // 1024)} KB\t"
              f"{info.get('reason', '')}")
    print(f"\n{len(names)} backups, newest last. Roll back one step: bm.py restore --last")


def cmd_backup(args):
    _, path = load_tree()
    dest, nodes = make_backup(path, args.reason)
    prune_backups()
    print(f"{dest}  ({nodes} nodes)")


def git_interrupted():
    """A rebase or merge left half-finished. Acting on top of one makes it worse."""
    git = os.path.join(DATA_DIR, ".git")
    for marker, name in (("rebase-merge", "rebase"), ("rebase-apply", "rebase"),
                         ("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick")):
        if os.path.exists(os.path.join(git, marker)):
            return name
    return None


def cmd_save(args):
    if not os.path.isdir(os.path.join(DATA_DIR, ".git")):
        die(f"{DATA_DIR} is not a git repository — the index has no history and "
            f"nothing to roll back to. See references/setup.md.")
    stuck = git_interrupted()
    if stuck:
        die(f"a {stuck} is in progress in {DATA_DIR}. Finish it first:\n"
            f"  cd {DATA_DIR} && git {stuck} --continue   # or --abort\n"
            f"Saving on top of it would strand your commit off any branch.")
    tracked = [f for f in ("index.jsonl", "profile.md", "config.json", ".gitignore")
               if os.path.exists(os.path.join(DATA_DIR, f))]
    if not tracked:
        die(f"nothing to save in {DATA_DIR}")

    # git add is atomic over its pathspecs: one missing file used to abort the
    # whole add while the command still reported success.
    add = subprocess.run(["git", "-C", DATA_DIR, "add"] + tracked,
                         capture_output=True, text=True)
    if add.returncode != 0:
        die(f"git add failed: {(add.stderr or add.stdout).strip()}")

    staged = subprocess.run(["git", "-C", DATA_DIR, "diff", "--cached", "--name-only"],
                            capture_output=True, text=True).stdout.split()
    if staged:
        res = subprocess.run(["git", "-C", DATA_DIR, "commit", "-m", args.message],
                             capture_output=True, text=True)
        if res.returncode != 0:
            die(f"git commit failed: {(res.stderr or res.stdout).strip()}")
        print(f"committed: {', '.join(staged)}")
    else:
        print("nothing changed since the last save")

    if args.no_push:
        return
    has_remote = subprocess.run(["git", "-C", DATA_DIR, "remote"],
                                capture_output=True, text=True).stdout.strip()
    if not has_remote:
        print("no remote configured; committed locally only")
        return
    # Reached even when nothing was committed just now: a commit that exists only
    # locally is one machine failure away from being the only copy.
    unpushed = subprocess.run(
        ["git", "-C", DATA_DIR, "log", "--oneline", "@{u}.."],
        capture_output=True, text=True)
    if not staged and unpushed.returncode == 0 and not unpushed.stdout.strip():
        print("remote is up to date")
        return

    branch = subprocess.run(
        ["git", "-C", DATA_DIR, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    remote_has_branch = subprocess.run(
        ["git", "-C", DATA_DIR, "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True).stdout.strip()

    # index.jsonl is one record per line keyed by guid, so a rebase conflict is
    # mechanically resolvable — but only if we find out about it here rather than
    # on the next machine. Nothing to rebase onto when the remote has no such
    # branch yet: that is a first push, not a divergence.
    pull = subprocess.run(["git", "-C", DATA_DIR, "pull", "--rebase"],
                          capture_output=True, text=True) if remote_has_branch else None
    if pull is not None and pull.returncode != 0:
        # Never leave the repo mid-rebase on a detached HEAD. Aborting restores a
        # clean branch with the commit safely on it — the user can then resolve
        # deliberately instead of being walked further into a broken state.
        subprocess.run(["git", "-C", DATA_DIR, "rebase", "--abort"],
                       capture_output=True, text=True)
        print(f"commit succeeded and is safe on {branch or 'your branch'}, "
              f"but the remote has "
              f"diverged:\n{(pull.stderr or pull.stdout).strip()}\n"
              f"  The rebase was aborted, so {DATA_DIR} is clean.\n"
              f"  Reconcile by hand:\n"
              f"    cd {DATA_DIR} && git pull --rebase\n"
              f"    # index.jsonl is one record per line keyed by guid: keep both\n"
              f"    # sides, delete the conflict markers, then\n"
              f"    git add index.jsonl && git rebase --continue && git push\n"
              f"  Then run `bm.py sync` to rebuild index.db.", file=sys.stderr)
        sys.exit(3)

    push_cmd = ["git", "-C", DATA_DIR, "push"]
    if not remote_has_branch and branch:
        push_cmd += ["-u", "origin", branch]   # first push needs the upstream set
    push = subprocess.run(push_cmd, capture_output=True, text=True)
    if push.returncode != 0:
        print(f"warning: commit succeeded but push failed:\n"
              f"{(push.stderr or push.stdout).strip()}", file=sys.stderr)
        sys.exit(3)
    print("pulled, rebased and pushed")


# ---------------------------------------------------------------- extension bridge
#
# Writes to a synced, account-backed Chrome MUST go through Chrome's own
# bookmarks API, not through the file — the file is not the source of truth and
# the server will overwrite external edits. The bridge is a localhost relay:
#   bm.py call  --(HTTP)-->  bm.py bridge  --(WebSocket)-->  extension  --> chrome.bookmarks
# The agent is the brain; the extension only executes what it is told and reports
# back. Nothing listens beyond 127.0.0.1.

_WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_ext_sock = None                 # live socket to the extension, set on connect
_ext_lock = threading.Lock()
_pending = {}                    # request id -> response Queue


def _ws_send(sock, data: bytes):
    import struct
    header = bytearray([0x81])
    n = len(data)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)
    sock.sendall(bytes(header) + data)


def _ws_recv(sock):
    """One complete message, reassembling fragmented frames per RFC 6455.
    Chrome splits large payloads (a full bookmark tree) across frames, so reading
    a single frame would parse truncated JSON. Returns bytes, or None on close."""
    import struct

    def readn(n):
        buf = b""
        while len(buf) < n:
            c = sock.recv(n - len(buf))
            if not c:
                return None
            buf += c
        return buf

    chunks = []
    while True:
        h = readn(2)
        if not h:
            return None
        fin = h[0] & 0x80
        opcode = h[0] & 0x0F
        masked = h[1] & 0x80
        ln = h[1] & 0x7F
        if ln == 126:
            e = readn(2)
            if e is None:
                return None
            ln = struct.unpack(">H", e)[0]
        elif ln == 127:
            e = readn(8)
            if e is None:
                return None
            ln = struct.unpack(">Q", e)[0]
        mask = readn(4) if masked else b""
        if mask is None:
            return None
        payload = readn(ln) if ln else b""
        if payload is None:
            return None
        if masked and payload:
            payload = bytes(b ^ mask[i & 3] for i, b in enumerate(payload))
        if opcode == 0x8:            # close
            return None
        if opcode == 0x9:            # ping -> pong
            sock.sendall(bytes([0x8A, len(payload)]) + payload)
            continue
        if opcode == 0xA:            # pong
            continue
        chunks.append(payload)       # data frame (text/binary/continuation)
        if fin:
            return b"".join(chunks)


def cmd_bridge(args):
    import base64
    import hashlib
    import queue
    import uuid
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    global _ext_sock

    # Last real command (not the extension's keepalive) — drives idle shutdown.
    last_cmd = [time.monotonic()]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002 - match base signature
            pass

        def do_GET(self):
            global _ext_sock
            if self.headers.get("Upgrade", "").lower() != "websocket":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"bookmark bridge up")
                return
            key = self.headers.get("Sec-WebSocket-Key", "")
            accept = base64.b64encode(
                hashlib.sha1((key + _WS_MAGIC).encode()).digest()).decode()
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", accept)
            self.end_headers()
            self.close_connection = True
            sock = self.connection
            with _ext_lock:
                _ext_sock = sock
            print("extension connected", file=sys.stderr)
            try:
                while True:
                    msg = _ws_recv(sock)
                    if msg is None:
                        break
                    if not msg:
                        continue
                    data = json.loads(msg.decode("utf-8"))
                    q = _pending.get(data.get("id"))
                    if q:
                        q.put(data)
            except OSError:
                pass
            finally:
                with _ext_lock:
                    if _ext_sock is sock:
                        _ext_sock = None
                print("extension disconnected", file=sys.stderr)

        def do_POST(self):
            last_cmd[0] = time.monotonic()
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError as exc:
                return self._json({"error": f"bad json: {exc}"})
            rid = uuid.uuid4().hex
            q = queue.Queue()
            _pending[rid] = q
            with _ext_lock:
                sock = _ext_sock
            if sock is None:
                _pending.pop(rid, None)
                return self._json({"error": "extension not connected"})
            try:
                _ws_send(sock, json.dumps({"id": rid, **body}).encode("utf-8"))
            except OSError:
                _pending.pop(rid, None)
                return self._json({"error": "extension socket dead"})
            try:
                resp = q.get(timeout=args.timeout)
            except queue.Empty:
                resp = {"error": "timeout waiting for extension"}
            _pending.pop(rid, None)
            self._json(resp)

        def _json(self, obj):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"bridge listening on 127.0.0.1:{args.port}", file=sys.stderr)
    print("load/enable the extension now; it will connect automatically",
          file=sys.stderr)

    if args.idle and args.idle > 0:
        idle_seconds = args.idle * 60

        def watchdog():
            # The extension's 20s keepalive is deliberately NOT counted as
            # activity (it never touches do_POST), so a connected-but-unused
            # bridge still times out. `ensure_bridge` restarts it on next use.
            while True:
                time.sleep(30)
                if time.monotonic() - last_cmd[0] >= idle_seconds:
                    print(f"idle for {args.idle} min with no commands — "
                          f"shutting down", file=sys.stderr)
                    srv.shutdown()
                    return

        threading.Thread(target=watchdog, daemon=True).start()

    srv.serve_forever()


def cmd_call(args):
    import http.client
    ensure_bridge(args.port)
    payload = args.json if args.json else json.dumps(
        {"cmd": args.cmd, "args": json.loads(args.args)} if args.args
        else {"cmd": args.cmd})
    conn = http.client.HTTPConnection("127.0.0.1", args.port, timeout=args.timeout + 5)
    conn.request("POST", "/call", payload,
                 {"Content-Type": "application/json"})
    resp = conn.getresponse().read().decode("utf-8")
    conn.close()
    print(resp)


def _bridge_is_up(port):
    """True if the relay is listening and answering on 127.0.0.1:port."""
    import http.client
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
        conn.request("GET", "/")
        conn.getresponse().read()
        conn.close()
        return True
    except OSError:
        return False


def _extension_connected(port):
    """Ping through the relay; True only if the extension answered."""
    import http.client
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("POST", "/call", json.dumps({"cmd": "ping"}),
                     {"Content-Type": "application/json"})
        r = json.loads(conn.getresponse().read().decode("utf-8"))
        conn.close()
        return isinstance(r, dict) and not r.get("error")
    except OSError:
        return False


def ensure_bridge(port):
    """Make sure the relay is running before a call needs it. If nothing is
    listening, spawn a detached `bm.py bridge` and wait for it to accept
    connections; then give a loaded extension a moment to (re)connect its
    socket. Returns True once the relay is up. Starting the relay does not load
    the Chrome extension — that is the user's one manual step — so a running
    relay with no extension still surfaces "extension not connected"."""
    if _bridge_is_up(port):
        return True
    log_path = os.path.join(DATA_DIR, "bridge.log")
    try:
        logf = open(log_path, "ab")  # noqa: SIM115 - handed to the child process
    except OSError:
        logf = subprocess.DEVNULL
    subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "bridge", "--port", str(port)],
        stdout=logf, stderr=logf, stdin=subprocess.DEVNULL, start_new_session=True)
    print(f"bridge was not running — started it on 127.0.0.1:{port} "
          f"(log: {log_path})", file=sys.stderr)
    for _ in range(50):  # up to ~5s for the relay to bind
        if _bridge_is_up(port):
            break
        time.sleep(0.1)
    else:
        return False
    for _ in range(40):  # up to ~8s for a loaded extension to reconnect
        if _extension_connected(port):
            break
        time.sleep(0.2)
    return True


def _bridge_call(port, cmd, cargs=None, timeout=60):
    """Send one command to the extension via the bridge; return its parsed reply.
    Auto-starts the relay if it is not already running."""
    import http.client
    ensure_bridge(port)
    body = json.dumps({"cmd": cmd, "args": cargs or {}})
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout + 5)
        conn.request("POST", "/call", body, {"Content-Type": "application/json"})
        resp = json.loads(conn.getresponse().read().decode("utf-8"))
        conn.close()
    except OSError as exc:
        die(f"cannot reach the bridge on 127.0.0.1:{port} ({exc}) even after trying "
            f"to start it. Start it by hand with: bm.py bridge")
    if isinstance(resp, dict) and resp.get("error"):
        die(f"extension error: {resp['error']}")
    if isinstance(resp, dict) and "result" in resp:
        return resp["result"]
    return resp


def _flatten_live(tree):
    """chrome.bookmarks tree -> (url -> [node ids], node id -> {title,path})."""
    by_url, info = {}, {}

    def walk(nodes, path):
        for n in nodes:
            if n.get("url"):
                by_url.setdefault(n["url"], []).append(n["id"])
                info[n["id"]] = {"title": n.get("title", ""), "path": path}
            if n.get("children"):
                walk(n["children"], path + " › " + (n.get("title") or ""))
    walk(tree, "")
    return by_url, info


def cmd_apply_live(args):
    """Apply a delete patch through the running extension, so changes go through
    Chrome's own API and survive sync. Ops are matched to live nodes by URL,
    resolved from the index by guid — chrome.bookmarks node ids are not the guids
    the report emits."""
    with open(args.patch, encoding="utf-8") as fh:
        payload = json.load(fh)
    ops = payload["ops"] if isinstance(payload, dict) else payload
    deletes = [o for o in ops if o.get("op") == "delete"]
    other = [o for o in ops if o.get("op") != "delete"]
    if other:
        print(f"note: {len(other)} non-delete ops ignored — apply-live handles "
              f"deletes only for now", file=sys.stderr)
    if not deletes:
        die("no delete ops in the patch")

    recs = read_index()
    tree = _bridge_call(args.port, "tree")
    by_url, info = _flatten_live(tree)

    resolved, missing_url, not_live = [], [], []
    for o in deletes:
        rec = recs.get(o.get("guid"))
        url = (rec or {}).get("url") or o.get("url")
        if not url:
            missing_url.append(o)
            continue
        ids = by_url.get(url) or by_url.get(url.rstrip("/")) or []
        if not ids:
            not_live.append((o, url))
            continue
        for nid in ids:
            resolved.append((nid, url, o))

    dupes = sum(1 for u in {r[1] for r in resolved} if len(by_url.get(u, [])) > 1)
    print(f"patch deletes         : {len(deletes)}")
    print(f"resolved to live nodes: {len(resolved)}")
    if dupes:
        print(f"  ({dupes} of these URLs exist more than once live — every copy "
              f"will be removed)")
    if missing_url:
        print(f"no url in index/patch : {len(missing_url)} (skipped)")
    if not_live:
        print(f"not present in Chrome : {len(not_live)} (already gone; skipped)")

    from collections import Counter
    br = Counter((info.get(nid, {}).get("path", "") or "").split(" › ")[1:3]
                 and " › ".join((info.get(nid, {}).get("path", "")).split(" › ")[1:3])
                 for nid, _, _ in resolved)
    print("\nby branch:")
    for b, c in br.most_common(12):
        print(f"  {c:5}  {b}")

    if not args.go:
        print(f"\npreview only — nothing removed. Re-run with --go to delete "
              f"{len(resolved)} nodes through Chrome.")
        return

    backup_account_store("before apply-live")
    done = errors = 0
    for nid, _, _ in resolved:
        r = _bridge_call(args.port, "remove", {"id": nid})
        if isinstance(r, dict) and r.get("error"):
            errors += 1
        else:
            done += 1
        if done % 50 == 0:
            print(f"  removed {done}/{len(resolved)}", file=sys.stderr)
    print(f"\nremoved {done} nodes через Chrome"
          + (f", {errors} errors" if errors else "")
          + ". Sync will carry the deletions to the account and other devices.")


def cmd_exec(args):
    """Execute id-based structural ops through the extension: remove empty folders,
    move nodes, rename/retitle. Previews by default; --go executes after a backup.
    Ops reference live chrome.bookmarks ids (from `call tree`), not guids."""
    with open(args.ops, encoding="utf-8") as fh:
        payload = json.load(fh)
    ops = payload["ops"] if isinstance(payload, dict) else payload

    tree = _bridge_call(args.port, "tree")
    info = {}

    def w(n, path):
        info[n["id"]] = {"title": n.get("title", ""), "url": n.get("url"),
                         "path": path, "kids": len(n.get("children", []))}
        for c in n.get("children", []):
            w(c, path + " › " + (n.get("title") or ""))
    for root in tree:
        w(root, "")

    lines, bad = [], []
    for i, o in enumerate(ops):
        op = o.get("op")
        nid = o.get("id")
        cur = info.get(nid)
        if cur is None:
            bad.append(f"op #{i}: id {nid} not in live tree")
            continue
        if op == "remove":
            if cur["kids"]:
                bad.append(f"op #{i}: {cur['title']!r} is not empty "
                           f"({cur['kids']} inside) — refusing to remove")
            else:
                lines.append(f"remove  {cur['title']!r}  ({cur['path'].strip(' ›')})")
        elif op == "move":
            dest = info.get(o.get("parentId"))
            if not dest or dest.get("url"):
                bad.append(f"op #{i}: move target {o.get('parentId')} not a folder")
            else:
                at = f" @{o['index']}" if o.get("index") is not None else ""
                lines.append(f"move    {cur['title']!r} -> {dest['title']!r}{at}")
        elif op == "update":
            new = o.get("title")
            lines.append(f"rename  {cur['title']!r} -> {new!r}")
        else:
            bad.append(f"op #{i}: unknown op {op!r}")

    if bad:
        print("REFUSING — problems found, nothing executed:")
        for b in bad:
            print("  " + b)
        sys.exit(2)

    print(f"{len(lines)} operations:")
    for ln in lines[:args.show]:
        print("  " + ln)
    if len(lines) > args.show:
        print(f"  … and {len(lines) - args.show} more")

    if not args.go:
        print("\npreview only — re-run with --go to execute through Chrome.")
        return

    backup_account_store(f"before exec of {len(ops)} ops")
    done = errors = 0
    for o in ops:
        op = o.get("op")
        if op == "remove":
            r = _bridge_call(args.port, "remove", {"id": o["id"]})
        elif op == "move":
            dest = {"parentId": o["parentId"]}
            if o.get("index") is not None:
                dest["index"] = o["index"]
            r = _bridge_call(args.port, "move", {"id": o["id"], "dest": dest})
        elif op == "update":
            r = _bridge_call(args.port, "update",
                             {"id": o["id"], "changes": {"title": o["title"]}})
        else:
            r = {"error": "unknown"}
        if isinstance(r, dict) and r.get("error"):
            errors += 1
            print(f"  error on {op} {o.get('id')}: {r['error']}", file=sys.stderr)
        else:
            done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(ops)}", file=sys.stderr)
    print(f"\ndone: {done} applied"
          + (f", {errors} errors" if errors else "")
          + ". Sync carries the changes to the account and other devices.")


def backup_account_store(reason):
    """Copy the live account store aside before a live mutation."""
    acct = account_bookmarks_path()
    if not acct:
        return None
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUPS, f"AccountBookmarks.{stamp}")
    shutil.copy2(acct, dest)
    print(f"backup: {dest}", file=sys.stderr)
    return dest


def cmd_status(args):
    recs = read_index()
    enriched = len([r for r in recs.values() if r.get("tags")])
    running, why = chrome_process_state()
    bypass = os.environ.get("BM_ALLOW_RUNNING") == "1"
    backups = list_backups()

    print(f"data dir        {DATA_DIR}")
    print(f"bookmarks file  {bookmarks_path()}"
          + ("" if os.path.exists(bookmarks_path()) else "   <-- NOT FOUND"))
    print(f"profile.md      {'yes' if os.path.exists(os.path.join(DATA_DIR, 'profile.md')) else 'MISSING — run setup'}")
    print(f"index.jsonl     {len(recs) if recs else 'MISSING'} records, "
          f"{enriched} enriched")
    print(f"index.db        {'yes' if os.path.exists(DB) else 'MISSING — run sync'}")
    if os.path.isdir(os.path.join(DATA_DIR, ".git")):
        stuck = git_interrupted()
        print(f"git             {'INTERRUPTED — ' + stuck + ' in progress' if stuck else 'yes'}")
    else:
        print("git             NOT a repo — no index history")
    print(f"chrome          {'RUNNING' if running else 'not running'} ({why})")
    print(f"writes          {'BLOCKED while Chrome runs' if running and not bypass else 'allowed'}")
    if bypass:
        print("  !! BM_ALLOW_RUNNING=1 is set: the Chrome guard is DISABLED. "
              "Unset it before touching a live profile.")
    print(f"backups         {len(backups)}"
          + (f", newest {backups[-1]}" if backups else " — none yet"))


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(prog="bm.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="paths and readiness").set_defaults(fn=cmd_status)

    p = sub.add_parser("bridge", help="run the localhost relay for the Chrome extension")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--idle", type=int, default=30,
                   help="exit after this many minutes with no commands (0 = never)")
    p.set_defaults(fn=cmd_bridge)

    p = sub.add_parser("call", help="send one command to the extension via the bridge")
    p.add_argument("cmd", nargs="?", help="command name, e.g. ping / tree / remove")
    p.add_argument("--args", help="JSON object of arguments")
    p.add_argument("--json", help="full request JSON (overrides cmd/--args)")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(fn=cmd_call)
    sub.add_parser("stats", help="tree size and health metrics").set_defaults(fn=cmd_stats)
    sub.add_parser("profile-scan",
                   help="evidence pack for the setup interview").set_defaults(fn=cmd_profile_scan)

    p = sub.add_parser("tree", help="folder tree with counts and thin-folder flags")
    p.add_argument("--depth", type=int, default=3)
    p.set_defaults(fn=cmd_tree)

    p = sub.add_parser("folder", help="list bookmarks under a path substring or parent guid")
    p.add_argument("target")
    p.set_defaults(fn=cmd_folder)

    p = sub.add_parser("sync", help="refresh index from Chrome, rebuild db")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--prune", action="store_true",
                   help="really drop index records whose bookmarks are gone")
    p.set_defaults(fn=cmd_sync)

    p = sub.add_parser("dump", help="emit bookmarks needing enrichment as TSV")
    p.add_argument("--all", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(fn=cmd_dump)

    p = sub.add_parser("ingest", help="merge enrichment JSONL into the index")
    p.add_argument("file", nargs="?", default="-")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("search", help="FTS5 candidate retrieval")
    p.add_argument("terms", nargs="+")
    p.add_argument("-n", type=int, default=60)
    p.add_argument("--root")
    p.add_argument("--phrase", action="store_true",
                   help="match the words as an exact sequence instead of OR")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("check-links", help="HTTP sweep, cached in the index")
    p.add_argument("--cold", action="store_true", help="only never-opened 3y+ bookmarks")
    p.add_argument("--recheck", action="store_true")
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--accept-dns-failures", action="store_true",
                   help="write the run even if many domains fail to resolve")
    p.add_argument("--no-report", action="store_true",
                   help="skip writing the HTML report afterwards")
    p.set_defaults(fn=cmd_check_links)

    p = sub.add_parser("report", help="cleanup candidates grouped by reason")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--html", nargs="?", const="", default=None, metavar="PATH",
                   help="write the browsable HTML report instead of printing TSV")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("apply", help="apply a patch file to the Bookmarks file")
    p.add_argument("patch")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-file", action="store_true",
                   help="write the file even under account sync (will not stick)")
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("apply-live",
                       help="apply a patch through the running extension (sync-safe)")
    p.add_argument("patch")
    p.add_argument("--go", action="store_true",
                   help="actually execute; without it, only resolves and previews")
    p.add_argument("--port", type=int, default=8787)
    p.set_defaults(fn=cmd_apply_live)

    p = sub.add_parser("exec", help="run id-based structural ops through the extension")
    p.add_argument("ops", help="JSON file of {ops:[{op,id,...}]}")
    p.add_argument("--go", action="store_true", help="execute; default is preview")
    p.add_argument("--show", type=int, default=60, help="how many ops to print")
    p.add_argument("--port", type=int, default=8787)
    p.set_defaults(fn=cmd_exec)

    p = sub.add_parser("backup", help="copy Bookmarks into backups/")
    p.add_argument("reason", nargs="?", default="manual")
    p.set_defaults(fn=cmd_backup)

    sub.add_parser("backups", help="list backups, newest last").set_defaults(fn=cmd_backups)

    p = sub.add_parser("restore", help="restore Bookmarks from a backup")
    p.add_argument("backup", nargs="?", help="filename; omit to use the newest")
    p.add_argument("--last", action="store_true", help="roll back one step")
    p.set_defaults(fn=cmd_restore)

    p = sub.add_parser("save", help="commit and push index.jsonl")
    p.add_argument("message", nargs="?", default="index update")
    p.add_argument("--no-push", action="store_true")
    p.set_defaults(fn=cmd_save)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Normal when output is piped into head/less. Avoid the interpreter's
        # "Exception ignored" noise on shutdown.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)

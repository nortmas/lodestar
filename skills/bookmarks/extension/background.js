// Thin executor. The brain is the agent driving bm.py; this only runs the
// chrome.bookmarks calls it is told to and reports back. No UI, no autonomy,
// no network beyond the localhost bridge. An open WebSocket also keeps the MV3
// service worker alive while a session is in progress.

const BRIDGE = "ws://127.0.0.1:8787/";
let ws = null;
let heartbeat = null;

function connect() {
  // Never stack a second socket on top of a live one.
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }
  try {
    ws = new WebSocket(BRIDGE);
  } catch (e) {
    setTimeout(connect, 2000);
    return;
  }
  ws.onopen = () => {
    // MV3 kills an idle service worker after ~30s, which would drop the socket.
    // Traffic on the port resets that timer, so a heartbeat keeps the worker —
    // and the connection — alive for as long as the bridge is up.
    clearInterval(heartbeat);
    heartbeat = setInterval(() => {
      try { ws.send(JSON.stringify({ keepalive: true })); } catch {}
    }, 20000);
  };
  ws.onmessage = async (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    if (msg.keepalive) return;
    const { id, cmd, args } = msg;
    try {
      const result = await run(cmd, args || {});
      ws.send(JSON.stringify({ id, result }));
    } catch (err) {
      ws.send(JSON.stringify({ id, error: String((err && err.message) || err) }));
    }
  };
  ws.onclose = () => { clearInterval(heartbeat); ws = null; setTimeout(connect, 2000); };
  ws.onerror = () => { try { ws.close(); } catch {} };
}

// Reconnect when Chrome wakes the worker for any reason.
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);

// The heartbeat above only keeps an ALREADY-connected worker alive. Once the
// socket drops (e.g. the bridge was restarted) an idle worker is reaped and has
// nothing left to fire setTimeout — so it never reconnects on its own. An alarm
// is the one thing that wakes a dead MV3 worker: it fires every minute (the
// platform minimum), reviving the worker so `connect()` can re-establish the
// socket against a freshly-started bridge. This is what makes the skill's
// auto-start of the bridge actually reconnect without the user touching Chrome.
chrome.alarms.create("reconnect", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((a) => { if (a.name === "reconnect") connect(); });

function bm(method, ...a) {
  return new Promise((resolve, reject) => {
    chrome.bookmarks[method](...a, (r) => {
      const e = chrome.runtime.lastError;
      if (e) reject(new Error(e.message)); else resolve(r);
    });
  });
}

// Every write command is here and nowhere else, so the surface is auditable.
async function run(cmd, args) {
  switch (cmd) {
    case "ping":       return { ok: true, ts: Date.now() };
    case "tree": {
      // Trim to what the agent needs (id for operations, url/title for matching).
      // The raw tree carries far more and bloats the payload.
      const raw = await bm("getTree");
      const trim = (n) => {
        const o = { id: n.id, title: n.title };
        if (n.url) o.url = n.url;
        if (n.children) o.children = n.children.map(trim);
        return o;
      };
      return raw.map(trim);
    }
    case "get":        return await bm("get", args.id);
    case "remove":     return await bm("remove", args.id);
    case "removeTree": return await bm("removeTree", args.id);
    case "move":       return await bm("move", args.id, args.dest);
    case "update":     return await bm("update", args.id, args.changes);
    case "create":     return await bm("create", args.node);
    default:           throw new Error("unknown cmd: " + cmd);
  }
}

connect();

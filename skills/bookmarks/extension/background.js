// Thin executor. The brain is the agent driving bm.py; this only runs the
// chrome.bookmarks calls it is told to and reports back. No UI, no autonomy,
// no network beyond the localhost bridge. An open WebSocket also keeps the MV3
// service worker alive while a session is in progress.

const BRIDGE = "ws://127.0.0.1:8787/";
let ws = null;

function connect() {
  try {
    ws = new WebSocket(BRIDGE);
  } catch (e) {
    setTimeout(connect, 2000);
    return;
  }
  ws.onmessage = async (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    const { id, cmd, args } = msg;
    try {
      const result = await run(cmd, args || {});
      ws.send(JSON.stringify({ id, result }));
    } catch (err) {
      ws.send(JSON.stringify({ id, error: String((err && err.message) || err) }));
    }
  };
  ws.onclose = () => { ws = null; setTimeout(connect, 2000); };
  ws.onerror = () => { try { ws.close(); } catch {} };
}

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
    case "tree":       return await bm("getTree");
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

"""Local web interface for App-Tracking-Logs.

Serves a single-page UI and streams captured GA4 / AppsFlyer / GTM events live to
the browser via Server-Sent Events (SSE). The capture itself is the existing
logic (adb / xcrun simctl); this module only orchestrates it and mirrors the
events that already flow through ``interface.show_log``.

Usage:
    python3 web_debug_logs.py [port]

Standard library only. Binds to localhost only.
"""

import json
import queue
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import capture_registry
from tools import capture_context, event_bus, process, ui_data, utils

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
_os = ui_data.OperatingSystem()

_capture_lock = threading.Lock()
# Tracks the current capture so we can tell an intentional Stop apart from a
# capture that ended on its own (e.g. no device connected).
_run_state = {"token": 0, "stopped": False}


def _start_capture(operating_system: str, platform: str) -> None:
    """Stop any running capture and start a new one in a daemon thread."""
    with _capture_lock:
        process.terminate_all()
        _run_state["token"] += 1
        _run_state["stopped"] = False
        token = _run_state["token"]

    def run() -> None:
        capture_context.set_context(operating_system, platform)
        started = time.monotonic()
        try:
            capture_registry.dispatch(operating_system, platform)
        except capture_registry.PlatformNotSupported:
            _publish_error(operating_system, platform,
                           "Plataforma não suportada para este sistema.")
            return
        except SystemExit:
            # A capture module called sys.exit on failure (e.g. missing adb/xcrun).
            _publish_error(operating_system, platform,
                           "Captura encerrada. Verifique adb/xcrun.")
            return
        except Exception as error:  # noqa: BLE001 - surface anything to the UI
            _publish_error(operating_system, platform, str(error))
            return

        # dispatch() returned = the log stream ended. If it ended quickly and the
        # user did not press Stop, the device/simulator is very likely missing.
        elapsed = time.monotonic() - started
        with _capture_lock:
            superseded = token != _run_state["token"]
            stopped = _run_state["stopped"]
        if not superseded and not stopped and elapsed < 3:
            _publish_error(operating_system, platform,
                           "Captura encerrou logo após iniciar. Há um device/emulador "
                           "conectado (adb) ou um Simulador iOS aberto?")

    threading.Thread(target=run, daemon=True).start()


def _stop_capture() -> None:
    """Mark the capture as intentionally stopped and terminate it."""
    with _capture_lock:
        _run_state["stopped"] = True
    process.terminate_all()


def _device_ready(operating_system: str) -> "tuple[bool, str]":
    """Check a device/simulator is available before starting a capture.

    Prevents the confusing "adb logcat waiting for device" silent state by
    giving the web UI immediate feedback. Returns ``(ok, message)``.
    """
    try:
        if operating_system == _os.ANDROID:
            out = subprocess.run(utils.COMMAND.LIST_ANDROID_DEVICES.value.split(" "),
                                 capture_output=True, text=True, timeout=10).stdout
            devices = [ln for ln in out.splitlines()[1:]
                       if ln.strip() and ln.split()[-1] == "device"]
            if not devices:
                return False, ("Nenhum device/emulador Android conectado. "
                               "Conecte um device (adb devices) e tente novamente.")
        elif operating_system == _os.IOS:
            out = subprocess.run(utils.COMMAND.LIST_IOS_BOOTED.value.split(" "),
                                 capture_output=True, text=True, timeout=15).stdout
            if "Booted" not in out:
                return False, ("Nenhum Simulador iOS aberto (booted). "
                               "Abra um Simulador e tente novamente.")
        else:
            return False, "Sistema operacional desconhecido."
    except FileNotFoundError:
        tool = "adb" if operating_system == _os.ANDROID else "xcrun"
        return False, f"'{tool}' não encontrado no PATH."
    except subprocess.TimeoutExpired:
        return False, "A verificação de device demorou demais. Tente novamente."
    return True, ""


def _publish_error(operating_system: str, platform: str, text: str) -> None:
    event_bus.publish({
        "os": operating_system,
        "platform": platform,
        "type": "error",
        "text": text,
    })


class Handler(BaseHTTPRequestHandler):
    """Routes: GET / , GET /api/platforms , GET /events (SSE) , POST /api/start|stop."""

    def log_message(self, *args) -> None:  # silence default request logging
        pass

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send_html()
        elif path == "/api/platforms":
            self._send_json(capture_registry.available())
        elif path == "/events":
            self._stream_events()
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?", 1)[0]
        if path == "/api/start":
            self._handle_start()
        elif path == "/api/stop":
            _stop_capture()
            self._send_json({"ok": True})
        else:
            self.send_error(404)

    # -- helpers -----------------------------------------------------------

    def _send_html(self) -> None:
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_start(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            self._send_json({"ok": False, "error": "invalid JSON"}, status=400)
            return

        operating_system = data.get("os")
        platform = data.get("platform")
        if platform not in capture_registry.enabled_platforms(operating_system):
            self._send_json({"ok": False, "error": "unsupported platform"}, status=400)
            return

        ready, message = _device_ready(operating_system)
        if not ready:
            self._send_json({"ok": False, "error": message}, status=409)
            return

        _start_capture(operating_system, platform)
        self._send_json({"ok": True, "os": operating_system, "platform": platform})

    def _stream_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        subscription = event_bus.subscribe()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    event = subscription.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")  # keep-alive
                    self.wfile.flush()
                    continue
                payload = json.dumps(event, ensure_ascii=False)
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ValueError):
            pass  # browser disconnected
        finally:
            event_bus.unsubscribe(subscription)


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    start_port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            start_port = int(sys.argv[1])
        except ValueError:
            print(f"Porta inválida: {sys.argv[1]}")
            sys.exit(1)

    server = None
    port = start_port
    for candidate in range(start_port, start_port + 20):
        try:
            server = ThreadingHTTPServer((HOST, candidate), Handler)
            port = candidate
            break
        except OSError:
            continue

    if server is None:
        print("Nenhuma porta livre encontrada.")
        sys.exit(1)

    url = f"http://{HOST}:{port}"
    print(f"🦝 App-Tracking-Logs Web em {url}")
    print("   (Ctrl+C para encerrar)")
    threading.Timer(0.6, _open_browser, args=[url]).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        process.terminate_all()
        server.shutdown()


PAGE = r"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>App-Tracking-Logs</title>
<style>
  :root {
    --bg: #0f1117; --panel: #171a22; --panel2: #1f2330; --border: #2a2f3d;
    --text: #e6e8ee; --muted: #99a0b0; --accent: #6ea8fe;
    --screenview: #6ea8fe; --event: #f5c451; --automatic: #8b93a5;
    --highlight: #4fd18b; --error: #ff6b6b; --log: #c3c9d6;
    --pf-ga4: #f5c451; --pf-af: #4fd18b; --pf-gtm: #b892ff; --pf-gau: #6ea8fe; --pf-other: #8b93a5;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #f4f5f8; --panel: #ffffff; --panel2: #eef0f5; --border: #d9dde6;
      --text: #1b1e27; --muted: #5b6172; --accent: #2563eb;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); }
  header { position: sticky; top: 0; z-index: 5; background: var(--panel);
    border-bottom: 1px solid var(--border); padding: 12px 16px; }
  .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .brand { font-weight: 700; font-size: 16px; margin-right: 6px; }
  .brand small { font-weight: 400; color: var(--muted); }
  select, input[type=text], button {
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 7px 10px; font-size: 13px; outline: none; }
  input[type=text] { min-width: 220px; flex: 1; }
  button { cursor: pointer; }
  button:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); color: #0b1020; border-color: var(--accent); font-weight: 600; }
  button.danger { border-color: var(--error); color: var(--error); }
  button:disabled { opacity: .45; cursor: not-allowed; }
  .status { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 12px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--muted); }
  .dot.on { background: var(--highlight); }
  .dot.capturing { background: var(--event); animation: pulse 1.1s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
  .filters { margin-top: 10px; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px;
    font-size: 12px; cursor: pointer; color: var(--muted); background: var(--panel2); user-select: none; }
  .chip.active { color: var(--text); border-color: var(--accent); background: color-mix(in srgb, var(--accent) 18%, transparent); }
  .count { color: var(--muted); font-size: 12px; margin-left: auto; }
  main { padding: 14px 16px 60px; max-width: 1100px; margin: 0 auto; }
  .empty { color: var(--muted); text-align: center; padding: 60px 0; }
  .card { background: var(--panel); border: 1px solid var(--border); border-left-width: 4px;
    border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
  .card > details { margin: 0; }
  .card summary { list-style: none; cursor: pointer; padding: 10px 12px; display: flex; gap: 10px;
    align-items: center; }
  .card summary::-webkit-details-marker { display: none; }
  .badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; white-space: nowrap; }
  .badge.pf-ga4 { background: color-mix(in srgb, var(--pf-ga4) 22%, transparent); color: var(--pf-ga4); }
  .badge.pf-af  { background: color-mix(in srgb, var(--pf-af) 22%, transparent); color: var(--pf-af); }
  .badge.pf-gtm { background: color-mix(in srgb, var(--pf-gtm) 22%, transparent); color: var(--pf-gtm); }
  .badge.pf-gau { background: color-mix(in srgb, var(--pf-gau) 22%, transparent); color: var(--pf-gau); }
  .badge.pf-other { background: var(--panel2); color: var(--muted); }
  .ty { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  .title { flex: 1; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ts { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }
  pre { margin: 0; padding: 10px 12px 14px; background: var(--panel2); border-top: 1px solid var(--border);
    white-space: pre-wrap; word-break: break-word; font: 12.5px/1.5 "SF Mono", ui-monospace, Menlo, Consolas, monospace; }
  .toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
    background: var(--error); color: #fff; padding: 10px 16px; border-radius: 8px;
    box-shadow: 0 6px 20px rgba(0,0,0,.3); opacity: 0; transition: opacity .25s; pointer-events: none; }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
<header>
  <div class="row">
    <span class="brand">🦝 App-Tracking-Logs <small>web</small></span>
    <select id="os"></select>
    <select id="platform"></select>
    <button id="start" class="primary">▶ Iniciar</button>
    <button id="stop" class="danger" disabled>⏹ Parar</button>
    <span class="status"><span id="dot" class="dot"></span><span id="statusText">desconectado</span></span>
  </div>
  <div class="row filters">
    <input type="text" id="search" placeholder="Buscar nos eventos da sessão...">
    <button id="clear">Limpar</button>
    <span class="count"><span id="shown">0</span> / <span id="total">0</span> eventos</span>
  </div>
  <div class="row filters"><div class="chips" id="platformChips"></div></div>
  <div class="row filters"><div class="chips" id="typeChips"></div></div>
</header>
<main>
  <div id="list"></div>
  <div class="empty" id="empty">Escolha o sistema e a plataforma, clique em <b>Iniciar</b> e interaja com o app.</div>
</main>
<div class="toast" id="toast"></div>

<script>
(function () {
  var events = [];
  var localId = 0;
  var activePlatforms = new Set(); // empty = all
  var activeTypes = new Set();     // empty = all
  var seenPlatforms = new Set();
  var seenTypes = new Set();
  var platformsData = {};

  var $ = function (id) { return document.getElementById(id); };
  var listEl = $("list"), emptyEl = $("empty");

  function platformClass(p) {
    if (!p) return "pf-other";
    var s = ("" + p).toLowerCase();
    if (s.indexOf("appsflyer") >= 0) return "pf-af";
    if (s.indexOf("tag manager") >= 0 || s.indexOf("gtm") >= 0) return "pf-gtm";
    if (s.indexOf("universal") >= 0) return "pf-gau";
    if (s.indexOf("ga4") >= 0 || s.indexOf("firebase") >= 0) return "pf-ga4";
    return "pf-other";
  }

  function firstLine(text) {
    var lines = ("" + text).split("\n");
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim()) return lines[i].trim();
    }
    return "(vazio)";
  }

  function passesFilter(ev) {
    if (activePlatforms.size && !activePlatforms.has(ev.platform || "?")) return false;
    if (activeTypes.size && !activeTypes.has(ev.type || "log")) return false;
    var q = $("search").value.trim().toLowerCase();
    if (q) {
      var hay = ((ev.text || "") + " " + (ev.platform || "") + " " + (ev.type || "")).toLowerCase();
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  }

  function makeCard(ev) {
    var card = document.createElement("div");
    card.className = "card";
    card.style.borderLeftColor = "var(--" + (ev.type || "log") + ")";

    var det = document.createElement("details");
    det.open = true;
    var sum = document.createElement("summary");

    var badge = document.createElement("span");
    badge.className = "badge " + platformClass(ev.platform);
    badge.textContent = ev.platform || "?";

    var ty = document.createElement("span");
    ty.className = "ty";
    ty.textContent = ev.type || "log";

    var title = document.createElement("span");
    title.className = "title";
    title.textContent = firstLine(ev.text);

    var ts = document.createElement("span");
    ts.className = "ts";
    ts.textContent = ev.ts || "";

    sum.appendChild(badge); sum.appendChild(ty); sum.appendChild(title); sum.appendChild(ts);
    var pre = document.createElement("pre");
    pre.textContent = ev.text || "";
    det.appendChild(sum); det.appendChild(pre);
    card.appendChild(det);
    return card;
  }

  function nearBottom() {
    return (window.innerHeight + window.scrollY) >= (document.body.scrollHeight - 120);
  }

  function updateCounts() {
    $("total").textContent = events.length;
    var shown = listEl.childElementCount;
    $("shown").textContent = shown;
    emptyEl.style.display = shown ? "none" : "";
  }

  function renderAll() {
    listEl.innerHTML = "";
    var frag = document.createDocumentFragment();
    for (var i = 0; i < events.length; i++) {
      if (passesFilter(events[i])) frag.appendChild(makeCard(events[i]));
    }
    listEl.appendChild(frag);
    updateCounts();
  }

  function ensureChip(container, value, set, seen) {
    if (seen.has(value)) return;
    seen.add(value);
    var chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    chip.onclick = function () {
      if (set.has(value)) { set.delete(value); chip.classList.remove("active"); }
      else { set.add(value); chip.classList.add("active"); }
      renderAll();
    };
    container.appendChild(chip);
  }

  function onEvent(ev) {
    ev._id = ++localId;
    events.push(ev);
    ensureChip($("platformChips"), ev.platform || "?", activePlatforms, seenPlatforms);
    ensureChip($("typeChips"), ev.type || "log", activeTypes, seenTypes);
    if (passesFilter(ev)) {
      var stick = nearBottom();
      listEl.appendChild(makeCard(ev));
      updateCounts();
      if (stick) window.scrollTo(0, document.body.scrollHeight);
    } else {
      $("total").textContent = events.length;
    }
    if (ev.type === "error") toast(ev.text);
  }

  var toastTimer;
  function toast(msg) {
    var t = $("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 4000);
  }

  // --- SSE connection ---
  function connect() {
    var es = new EventSource("/events");
    es.onopen = function () { setStatus("on", "conectado"); };
    es.onmessage = function (e) {
      try { onEvent(JSON.parse(e.data)); } catch (err) {}
    };
    es.onerror = function () { setStatus("", "reconectando..."); };
  }

  var capturing = false;
  function setStatus(cls, text) {
    var dot = $("dot");
    dot.className = "dot" + (capturing ? " capturing" : (cls ? " " + cls : ""));
    $("statusText").textContent = capturing ? "capturando" : text;
  }

  // --- controls ---
  function populatePlatforms() {
    var os = $("os").value;
    var sel = $("platform");
    sel.innerHTML = "";
    (platformsData[os] || []).forEach(function (p) {
      var o = document.createElement("option");
      o.value = p; o.textContent = p; sel.appendChild(o);
    });
  }

  fetch("/api/platforms").then(function (r) { return r.json(); }).then(function (data) {
    platformsData = data;
    var osSel = $("os");
    Object.keys(data).forEach(function (os) {
      var o = document.createElement("option");
      o.value = os; o.textContent = os; osSel.appendChild(o);
    });
    populatePlatforms();
  });

  $("os").onchange = populatePlatforms;
  $("search").oninput = renderAll;
  $("clear").onclick = function () { events = []; renderAll(); };

  $("start").onclick = function () {
    var body = { os: $("os").value, platform: $("platform").value };
    fetch("/api/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.ok) {
          capturing = true;
          $("start").disabled = true; $("stop").disabled = false;
          setStatus("on", "capturando");
        } else { toast("Erro ao iniciar: " + (res.error || "desconhecido")); }
      })
      .catch(function () { toast("Falha na requisição de início."); });
  };

  $("stop").onclick = function () {
    fetch("/api/stop", { method: "POST" }).then(function () {
      capturing = false;
      $("start").disabled = false; $("stop").disabled = true;
      setStatus("on", "parado");
    });
  };

  connect();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()

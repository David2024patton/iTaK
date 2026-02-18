function clampText(value, max = 120) {
    const text = String(value ?? "");
    return text.length > max ? `${text.slice(0, max)}…` : text;
}

function targetDescriptor(target) {
    if (!target || !(target instanceof Element)) return "unknown";
    const tag = (target.tagName || "").toLowerCase();
    const id = target.id ? `#${target.id}` : "";
    const cls = target.className && typeof target.className === "string"
        ? `.${target.className.trim().split(/\s+/).slice(0, 2).join(".")}`
        : "";
    const role = target.getAttribute("role");
    const rolePart = role ? `[role=${role}]` : "";
    return `${tag}${id}${cls}${rolePart}` || "unknown";
}

function getSafeValue(target) {
    if (!target || !(target instanceof Element)) return "";
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
        return clampText(target.value || "", 60);
    }
    return "";
}

function shouldLogKey(event) {
    const key = event?.key || "";
    if (!key) return false;
    if (["Enter", "Escape", "Tab", "Backspace", "Delete"].includes(key)) return true;
    if (key.length === 1) return true;
    return false;
}

function serializeEvent(type, event) {
    const target = event?.target;
    const now = Date.now();
    const base = {
        ts: now,
        type,
        target: targetDescriptor(target),
        context: typeof globalThis.getContext === "function" ? globalThis.getContext() : null,
    };

    if (event instanceof MouseEvent || event instanceof PointerEvent || event instanceof TouchEvent) {
        const point = "changedTouches" in event && event.changedTouches?.length
            ? event.changedTouches[0]
            : event;
        base.x = Number(point?.clientX || 0);
        base.y = Number(point?.clientY || 0);
    }

    if (event instanceof PointerEvent) {
        base.pointer = event.pointerType || "unknown";
    }

    if (event instanceof KeyboardEvent) {
        base.key = clampText(event.key || "", 24);
        base.code = clampText(event.code || "", 24);
        base.ctrl = !!event.ctrlKey;
        base.shift = !!event.shiftKey;
        base.alt = !!event.altKey;
        base.meta = !!event.metaKey;
        if (!shouldLogKey(event)) return null;
    }

    if (type === "focusin" || type === "input") {
        const value = getSafeValue(target);
        if (value) base.value = value;
    }

    return base;
}

function formatEventLine(event) {
    const date = new Date(Number(event.ts || Date.now()));
    const hh = String(date.getHours()).padStart(2, "0");
    const mm = String(date.getMinutes()).padStart(2, "0");
    const ss = String(date.getSeconds()).padStart(2, "0");
    const ms = String(date.getMilliseconds()).padStart(3, "0");

    const parts = [`${hh}:${mm}:${ss}.${ms}`, event.type || "event", event.target || "unknown"];
    if (event.key) parts.push(`key=${event.key}`);
    if (event.pointer) parts.push(`ptr=${event.pointer}`);
    if (Number.isFinite(event.x) && Number.isFinite(event.y)) parts.push(`xy=${Math.round(event.x)},${Math.round(event.y)}`);
    return parts.join(" | ");
}

function createInteractionPanel(getEvents) {
    const root = document.createElement("div");
    root.id = "interaction-debug-panel";
    root.setAttribute("aria-live", "polite");
    root.style.cssText = [
        "position:fixed",
        "right:12px",
        "bottom:12px",
        "z-index:4600",
        "display:flex",
        "flex-direction:column",
        "gap:6px",
        "max-width:min(92vw,520px)",
        "font-family:var(--font-family-code, monospace)",
    ].join(";");

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.textContent = "Interactions";
    toggle.style.cssText = [
        "align-self:flex-end",
        "border:1px solid var(--color-border)",
        "background:var(--color-panel)",
        "color:var(--color-text)",
        "padding:6px 10px",
        "border-radius:8px",
        "cursor:pointer",
        "font-size:12px",
        "line-height:1",
    ].join(";");

    const panel = document.createElement("div");
    panel.style.cssText = [
        "display:none",
        "border:1px solid var(--color-border)",
        "background:var(--color-panel)",
        "color:var(--color-text)",
        "border-radius:10px",
        "padding:10px",
        "min-width:280px",
        "max-height:44vh",
        "overflow:auto",
        "box-shadow:0 6px 20px rgba(0,0,0,0.25)",
    ].join(";");

    const header = document.createElement("div");
    header.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:12px;opacity:.9;";
    header.innerHTML = "<strong>Interaction Trace</strong><span id=\"interaction-debug-count\">0</span>";

    const toolbar = document.createElement("div");
    toolbar.style.cssText = "display:flex;justify-content:flex-end;gap:8px;margin-bottom:8px;";

    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.textContent = "Copy";
    copyBtn.style.cssText = [
        "border:1px solid var(--color-border)",
        "background:var(--color-input)",
        "color:var(--color-text)",
        "padding:4px 8px",
        "border-radius:6px",
        "cursor:pointer",
        "font-size:11px",
        "line-height:1",
    ].join(";");

    const body = document.createElement("pre");
    body.style.cssText = "margin:0;font-size:11px;line-height:1.35;white-space:pre-wrap;word-break:break-word;";
    body.textContent = "No interactions yet.";

    panel.appendChild(header);
    toolbar.appendChild(copyBtn);
    panel.appendChild(toolbar);
    panel.appendChild(body);
    root.appendChild(toggle);
    root.appendChild(panel);
    document.body.appendChild(root);

    const stateKey = "interactionDebugPanelOpen";
    const initialOpen = localStorage.getItem(stateKey) === "1";

    function render() {
        const events = getEvents();
        const countEl = panel.querySelector("#interaction-debug-count");
        if (countEl) countEl.textContent = String(events.length);
        body.textContent = events.length
            ? events.map((evt) => formatEventLine(evt)).join("\n")
            : "No interactions yet.";
    }

    function setOpen(nextOpen) {
        panel.style.display = nextOpen ? "block" : "none";
        toggle.textContent = nextOpen ? "Interactions ✓" : "Interactions";
        localStorage.setItem(stateKey, nextOpen ? "1" : "0");
        if (nextOpen) render();
    }

    async function copyRecent() {
        const events = getEvents();
        const text = events.length
            ? events.map((evt) => formatEventLine(evt)).join("\n")
            : "No interactions yet.";
        try {
            await navigator.clipboard.writeText(text);
            copyBtn.textContent = "Copied";
            setTimeout(() => {
                copyBtn.textContent = "Copy";
            }, 1200);
        } catch (_e) {
            copyBtn.textContent = "Failed";
            setTimeout(() => {
                copyBtn.textContent = "Copy";
            }, 1200);
        }
    }

    toggle.addEventListener("click", () => {
        setOpen(panel.style.display === "none");
    });

    copyBtn.addEventListener("click", () => {
        copyRecent();
    });

    setOpen(initialOpen);

    return {
        render,
        isOpen: () => panel.style.display !== "none",
        setOpen,
    };
}

export function initInteractionLogger(options = {}) {
    if (globalThis.__interactionLoggerInitialized) return;
    globalThis.__interactionLoggerInitialized = true;

    const enabled = options.enabled ?? true;
    if (!enabled) return;

    const queue = [];
    const maxQueue = Number(options.maxQueue || 120);
    const maxBatch = Number(options.maxBatch || 30);
    const flushMs = Number(options.flushMs || 1200);
    const minGapMs = Number(options.minGapMs || 35);
    const lastByType = new Map();
    const recent = [];
    const maxRecent = Number(options.maxRecent || 10);
    let flushTimer = null;
    let panelApi = null;

    async function flush(reason = "timer") {
        if (!queue.length) return;
        const batch = queue.splice(0, maxBatch);
        try {
            if (typeof globalThis.sendJsonData === "function") {
                await globalThis.sendJsonData("/interaction_log", { events: batch, reason });
            } else if (typeof globalThis.fetchApi === "function") {
                await globalThis.fetchApi("/interaction_log", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ events: batch, reason }),
                });
            }
        } catch (_e) {
            if (queue.length < maxQueue) {
                queue.unshift(...batch);
            }
        }
    }

    function ensureTimer() {
        if (flushTimer !== null) return;
        flushTimer = window.setInterval(() => {
            flush("interval");
        }, flushMs);
    }

    function pushEvent(type, event) {
        const now = performance.now();
        const prev = lastByType.get(type) || 0;
        if (now - prev < minGapMs) return;
        lastByType.set(type, now);

        const serialized = serializeEvent(type, event);
        if (!serialized) return;

        recent.push(serialized);
        if (recent.length > maxRecent) {
            recent.splice(0, recent.length - maxRecent);
        }

        queue.push(serialized);
        if (queue.length > maxQueue) {
            queue.splice(0, queue.length - maxQueue);
        }
        if (queue.length >= maxBatch) {
            flush("batch");
        }

        if (panelApi && panelApi.isOpen()) {
            panelApi.render();
        }
    }

    const listenerOptions = { capture: true, passive: true };
    document.addEventListener("pointerdown", (e) => pushEvent("pointerdown", e), listenerOptions);
    document.addEventListener("click", (e) => pushEvent("click", e), listenerOptions);
    document.addEventListener("focusin", (e) => pushEvent("focusin", e), listenerOptions);
    document.addEventListener("touchstart", (e) => pushEvent("touchstart", e), listenerOptions);
    document.addEventListener("mousedown", (e) => pushEvent("mousedown", e), listenerOptions);
    document.addEventListener("keydown", (e) => pushEvent("keydown", e), true);
    document.addEventListener("input", (e) => pushEvent("input", e), listenerOptions);

    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden") {
            flush("hidden");
        }
    });

    window.addEventListener("beforeunload", () => {
        flush("beforeunload");
    });

    panelApi = createInteractionPanel(() => [...recent]);

    globalThis.getRecentInteractions = () => [...recent];
    globalThis.toggleInteractionPanel = () => {
        if (!panelApi) return;
        panelApi.setOpen(!panelApi.isOpen());
    };

    document.addEventListener("keydown", (event) => {
        if (event.ctrlKey && event.shiftKey && (event.key === "L" || event.key === "l")) {
            event.preventDefault();
            globalThis.toggleInteractionPanel();
        }
    }, true);

    ensureTimer();
}

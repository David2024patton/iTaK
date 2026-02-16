import { createStore } from "/js/AlpineStore.js";

let bootstrapTooltipObserver = null;

function ensureBootstrapTooltip(element) {
  if (!element || !(element instanceof Element)) return;
  
  const bs = globalThis.bootstrap;
  if (!bs?.Tooltip) return;

  const existing = bs.Tooltip.getInstance(element);
  const title = (element.getAttribute("title") || element.getAttribute("data-bs-original-title") || "").trim();

  if (!title) return;

  if (existing) {
    try {
      if (element.getAttribute("title")) {
        element.setAttribute("data-bs-original-title", title);
        element.removeAttribute("title");
      }
      existing.setContent({ ".tooltip-inner": title });
      return;
    } catch (_e) {
      // Instance is stale/broken; dispose and recreate.
      try {
        existing.dispose();
      } catch (_disposeError) {
        // no-op
      }
    }
  }

  if (element.getAttribute("title")) {
    element.setAttribute("data-bs-original-title", title);
    element.removeAttribute("title");
  }

  if (!element.hasAttribute("data-bs-toggle")) {
    element.setAttribute("data-bs-toggle", "tooltip");
  }
  element.setAttribute("data-bs-trigger", "hover");
  element.setAttribute("data-bs-tooltip-initialized", "true");
  try {
    new bs.Tooltip(element, {
      delay: { show: 0, hide: 0 },
      trigger: "hover",
      template: '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>',
    });
  } catch (_e) {
    element.removeAttribute("data-bs-tooltip-initialized");
  }
}

function initBootstrapTooltips(root = document) {
  if (!globalThis.bootstrap?.Tooltip) return;
  const tooltipTargets = root.querySelectorAll(
    "[title]:not([data-bs-tooltip-initialized]), [data-bs-original-title]:not([data-bs-tooltip-initialized])"
  );
  tooltipTargets.forEach((element) => ensureBootstrapTooltip(element));
}

function observeBootstrapTooltips() {
  if (!globalThis.bootstrap?.Tooltip) return;
  
  // Prevent multiple observers
  if (bootstrapTooltipObserver) return;
  
  bootstrapTooltipObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes" && ["title", "data-bs-original-title"].includes(mutation.attributeName)) {
        ensureBootstrapTooltip(mutation.target);
        return;
      }

      if (mutation.type === "childList") {
        // Check removed nodes for tooltip cleanup
        mutation.removedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          const tooltipElements = node.matches?.('[data-bs-tooltip-initialized]') ? [node] : Array.from(node.querySelectorAll?.('[data-bs-tooltip-initialized]') || []);
          tooltipElements.forEach((el) => {
            const instance = globalThis.bootstrap?.Tooltip?.getInstance(el);
            if (instance) {
              instance.dispose();
            }
          });
        });
        
        mutation.addedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          if (
            node.matches("[title], [data-bs-original-title]") ||
            node.querySelector("[title], [data-bs-original-title]")
          ) {
            initBootstrapTooltips(node);
          }
        });
      }
    });
  });

  bootstrapTooltipObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["title", "data-bs-original-title"],
  });
}

function cleanupTooltipObserver() {
  if (bootstrapTooltipObserver) {
    bootstrapTooltipObserver.disconnect();
    bootstrapTooltipObserver = null;
  }
}

export const store = createStore("tooltips", {
  init() {
    initBootstrapTooltips();
    observeBootstrapTooltips();
  },
  
  cleanup: cleanupTooltipObserver,
});

import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

function toast(text, type = "info", timeout = 3000) {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000);
}

const model = {
  apps: [],
  loading: false,
  syncing: false,
  refreshing: false,
  statusMessage: "",
  query: "",
  loadedOnce: false,

  get filteredApps() {
    const q = (this.query || "").toLowerCase().trim();
    const source = Array.isArray(this.apps) ? [...this.apps] : [];
    const normalized = source
      .filter((app) => app?.url)
      .sort((left, right) => {
        const leftName = String(left?.name || left?.id || "").toLowerCase();
        const rightName = String(right?.name || right?.id || "").toLowerCase();
        return leftName.localeCompare(rightName);
      });

    if (!q) return normalized;
    return normalized.filter((app) => {
      const name = String(app?.name || "").toLowerCase();
      const id = String(app?.id || "").toLowerCase();
      const url = String(app?.url || "").toLowerCase();
      return name.includes(q) || id.includes(q) || url.includes(q);
    });
  },

  async load() {
    this.loading = true;
    try {
      const response = await callJsonApi("launchpad_apps", {});
      this.apps = Array.isArray(response?.data) ? response.data : [];
      this.statusMessage = this.apps.length ? `${this.apps.length} apps loaded` : "No apps loaded";
      this.loadedOnce = true;
    } catch (_e) {
      this.apps = [];
      this.statusMessage = "Failed to load apps";
    } finally {
      this.loading = false;
    }
  },

  async ensureLoaded() {
    if (!this.loadedOnce) {
      await this.load();
    }
  },

  openApp(url) {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
  },

  async copyAppUrl(url) {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      toast("Link copied", "success", 1800);
    } catch (_e) {
      toast("Failed to copy link", "error", 2200);
    }
  },

  async refreshCatalog() {
    this.refreshing = true;
    this.statusMessage = "Refreshing catalog...";
    try {
      const response = await callJsonApi("catalog_refresh", {});
      if (response?.ok) {
        await this.load();
        toast("Catalog refreshed", "success", 2200);
        return true;
      }
      throw new Error(response?.error || "Catalog refresh failed");
    } catch (e) {
      this.statusMessage = e?.message || "Catalog refresh failed";
      toast(this.statusMessage, "error", 2800);
      return false;
    } finally {
      this.refreshing = false;
    }
  },

  async syncCatalog() {
    this.syncing = true;
    this.statusMessage = "Syncing from Cherry...";
    try {
      const response = await callJsonApi("catalog_sync_from_cherry", {});
      if (response?.ok) {
        await this.load();
        const providers = Number(response?.providers || 0);
        const models = Number(response?.models || 0);
        const minapps = Number(response?.minapps || 0);
        this.statusMessage = `Synced ${providers} providers, ${models} models, ${minapps} minapps`;
        toast("Catalog synced", "success", 2200);
        return true;
      }
      throw new Error(response?.error || "Catalog sync failed");
    } catch (e) {
      this.statusMessage = e?.message || "Catalog sync failed";
      toast(this.statusMessage, "error", 2800);
      return false;
    } finally {
      this.syncing = false;
    }
  },
};

export const store = createStore("launchpad", model);

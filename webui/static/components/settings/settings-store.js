import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

// Constants
const VIEW_MODE_STORAGE_KEY = "settingsActiveTab";
const DEFAULT_TAB = "agent";

// Field button actions (field id -> modal path)
const FIELD_BUTTON_MODAL_BY_ID = Object.freeze({
  mcp_servers_config: "settings/mcp/client/mcp-servers.html",
  backup_create: "settings/backup/backup.html",
  backup_restore: "settings/backup/restore.html",
  show_a2a_connection: "settings/a2a/a2a-connection.html",
  external_api_examples: "settings/external/api-examples.html",
});

const SYSTEM_TEST_COMMANDS = Object.freeze({
  resources: "bash tools/check_resource_endpoints.sh",
  memory: "bash tools/check_memory_smoke.sh",
  chat: "bash tools/check_chat_smoke.sh",
  all: "bash tools/check_system_smoke.sh",
});

// Helper for toasts
function toast(text, type = "info", timeout = 5000) {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000);
}

// Settings Store
const model = {
  // State
  isLoading: false,
  error: null,
  settings: null,
  additional: null,
  catalogSyncing: false,
  catalogSyncMessage: "",
  minappsList: [],
  minappsLoading: false,
  minappsQuery: "",
  workdirFileStructureTestOutput: "",
  systemTestRunning: false,
  systemTestOutput: "",
  systemTestCommand: "",
  systemTestExitCode: null,
  systemTestLastRun: "",
  
  // Tab state
  _activeTab: DEFAULT_TAB,
  get activeTab() {
    return this._activeTab;
  },
  set activeTab(value) {
    const previous = this._activeTab;
    this._activeTab = value;
    this.applyActiveTab(previous, value);
  },

  // Lifecycle
  init() {
    // Restore persisted tab
    try {
      const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
      if (saved) this._activeTab = saved;
    } catch {}
  },

  async onOpen() {
    this.error = null;
    this.isLoading = true;
    
    try {
      const response = await API.callJsonApi("settings_get", null);
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || null;
      } else {
        throw new Error("Invalid settings response");
      }
    } catch (e) {
      console.error("Failed to load settings:", e);
      this.error = e.message || "Failed to load settings";
      toast("Failed to load settings", "error");
    } finally {
      this.isLoading = false;
    }

    // Trigger tab activation for current tab
    this.applyActiveTab(null, this._activeTab);
  },

  cleanup() {
    this.settings = null;
    this.additional = null;
    this.error = null;
    this.isLoading = false;
  },

  // Tab management
  applyActiveTab(previous, current) {
    // Persist
    try {
      localStorage.setItem(VIEW_MODE_STORAGE_KEY, current);
    } catch {}
  },

  switchTab(tabName) {
    this.activeTab = tabName;
  },



  get apiKeyProviders() {
    const seen = new Set();
    const options = [];
    const addProvider = (prov) => {
      if (!prov?.value) return;
      const key = prov.value.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      options.push({ value: prov.value, label: prov.label || prov.value });
    };
    (this.additional?.chat_providers || []).forEach(addProvider);
    (this.additional?.embedding_providers || []).forEach(addProvider);
    options.sort((a, b) => a.label.localeCompare(b.label));
    return options;
  },

  get filteredMinapps() {
    const query = (this.minappsQuery || "").toLowerCase().trim();
    const list = Array.isArray(this.minappsList) ? this.minappsList : [];
    if (!query) return list;
    return list.filter((item) => {
      const id = String(item?.id || "").toLowerCase();
      const name = String(item?.name || "").toLowerCase();
      const url = String(item?.url || "").toLowerCase();
      return id.includes(query) || name.includes(query) || url.includes(query);
    });
  },

  // Save settings
  async saveSettings() {
    if (!this.settings) {
      toast("No settings to save", "warning");
      return false;
    }

    this.isLoading = true;
    try {
      const response = await API.callJsonApi("settings_set", { settings: this.settings });
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || this.additional;
        toast("Settings saved successfully", "success");
        document.dispatchEvent(
          new CustomEvent("settings-updated", { detail: response.settings })
        );
        return true;
      } else {
        throw new Error("Failed to save settings");
      }
    } catch (e) {
      console.error("Failed to save settings:", e);
      toast("Failed to save settings: " + e.message, "error");
      return false;
    } finally {
      this.isLoading = false;
    }
  },

  // Close the modal
  closeSettings() {
    window.closeModal("settings/settings.html");
  },

  // Save and close
  async saveAndClose() {
    const success = await this.saveSettings();
    if (success) {
      this.closeSettings();
    }
  },

  async saveAndRunTests() {
    const success = await this.saveSettings();
    if (!success) return false;

    this.switchTab("external");
    setTimeout(() => {
      const target = document.getElementById("section-system-smoke-tests");
      if (target && typeof target.scrollIntoView === "function") {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        const previousOutline = target.style.outline;
        const previousOutlineOffset = target.style.outlineOffset;
        const previousTransition = target.style.transition;
        target.style.transition = "outline-color 200ms ease";
        target.style.outline = "2px solid var(--color-border)";
        target.style.outlineOffset = "6px";
        setTimeout(() => {
          target.style.outline = previousOutline;
          target.style.outlineOffset = previousOutlineOffset;
          target.style.transition = previousTransition;
        }, 1200);
      }
    }, 0);
    return await this.runSystemTest("all");
  },

  async syncCherryCatalog() {
    this.catalogSyncing = true;
    this.catalogSyncMessage = "";
    try {
      const response = await API.callJsonApi("catalog_sync_from_cherry", {});
      if (response?.ok) {
        if (response.additional) this.additional = response.additional;
        await this.loadMinapps();
        this.catalogSyncMessage = `Synced ${response.providers || 0} providers, ${response.models || 0} models, ${response.minapps || 0} minapps`;
        toast("Cherry catalog synced", "success");
        return true;
      }
      throw new Error(response?.error || "Catalog sync failed");
    } catch (e) {
      this.catalogSyncMessage = e.message || "Catalog sync failed";
      toast("Catalog sync failed: " + (e.message || "unknown error"), "error");
      return false;
    } finally {
      this.catalogSyncing = false;
    }
  },

  async refreshCatalog() {
    try {
      const response = await API.callJsonApi("catalog_refresh", {});
      if (response?.ok) {
        if (response.additional) this.additional = response.additional;
        await this.loadMinapps();
        toast("Catalog refreshed", "success", 2500);
        return true;
      }
      throw new Error(response?.error || "Catalog refresh failed");
    } catch (e) {
      toast("Catalog refresh failed: " + (e.message || "unknown error"), "error");
      return false;
    }
  },

  async loadMinapps() {
    this.minappsLoading = true;
    try {
      const response = await API.callJsonApi("minapps", {});
      this.minappsList = Array.isArray(response?.data) ? response.data : [];
      return true;
    } catch (e) {
      this.minappsList = [];
      return false;
    } finally {
      this.minappsLoading = false;
    }
  },

  getSystemTestCommand(testName) {
    return SYSTEM_TEST_COMMANDS[testName] || "";
  },

  async copySystemTestCommand(testName) {
    const command = this.getSystemTestCommand(testName);
    if (!command) {
      toast("Unknown test command", "warning", 2000);
      return;
    }
    try {
      await navigator.clipboard.writeText(command);
      toast("Command copied", "success", 1800);
    } catch (_e) {
      toast("Failed to copy command", "error", 2200);
    }
  },

  async runSystemTest(testName) {
    if (this.systemTestRunning) return false;
    const command = this.getSystemTestCommand(testName);
    if (!command) {
      toast("Unknown test", "warning", 2000);
      return false;
    }

    this.systemTestRunning = true;
    this.systemTestLastRun = testName;
    this.systemTestCommand = command;
    this.systemTestOutput = "Running test...";
    this.systemTestExitCode = null;

    try {
      const response = await API.callJsonApi("system_test_run", { test: testName });
      const output = response?.output || response?.error || "No output";
      this.systemTestOutput = output;
      this.systemTestExitCode = Number.isFinite(response?.exit_code) ? response.exit_code : null;

      if (response?.ok) {
        toast(`System test passed: ${testName}`, "success", 2200);
        return true;
      }

      toast(`System test failed: ${testName}`, "error", 2600);
      return false;
    } catch (e) {
      this.systemTestOutput = e?.message || "Failed to run system test";
      this.systemTestExitCode = -1;
      toast("Failed to run system test", "error", 2600);
      return false;
    } finally {
      this.systemTestRunning = false;
    }
  },

  async testWorkdirFileStructure() {
    if (!this.settings) return;
    try {
      const response = await API.callJsonApi("settings_workdir_file_structure", {
        workdir_path: this.settings.workdir_path,
        workdir_max_depth: this.settings.workdir_max_depth,
        workdir_max_files: this.settings.workdir_max_files,
        workdir_max_folders: this.settings.workdir_max_folders,
        workdir_max_lines: this.settings.workdir_max_lines,
        workdir_gitignore: this.settings.workdir_gitignore,
      });
      this.workdirFileStructureTestOutput = response?.data || "";
      window.openModal("settings/agent/workdir-file-structure-test.html");
    } catch (e) {
      console.error("Error testing workdir file structure:", e);
      toast("Error testing workdir file structure", "error");
    }
  },

  // Field helpers for external components
  // Handle button field clicks (opens sub-modals)
  async handleFieldButton(field) {
    const modalPath = FIELD_BUTTON_MODAL_BY_ID[field?.id];
    if (modalPath) window.openModal(modalPath);
  },

  // Open settings modal from external callers
  async open(initialTab = null) {
    if (initialTab) {
      this._activeTab = initialTab;
    }
    await window.openModal("settings/settings.html");
  },
};

const store = createStore("settings", model);

export { store };


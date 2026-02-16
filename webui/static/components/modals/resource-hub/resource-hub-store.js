import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
  isLoading: false,
  activeSection: "overview",
  data: {
    adapters: [],
    prompts: [],
    tools: [],
    skills: [],
    tasks: [],
    mcp: { configured: 0, connected: 0, total_tools: 0 },
  },
  preview: {
    kind: "",
    name: "",
    content: "",
  },

  get currentList() {
    if (this.activeSection === "overview") return [];
    return this.data[this.activeSection] || [];
  },

  async open(section = "overview") {
    this.activeSection = section;
    await this.load();
    await window.openModal("modals/resource-hub/resource-hub-modal.html");
  },

  async load() {
    this.isLoading = true;
    try {
      const response = await callJsonApi("/resource_hub", {});
      if (response?.ok && response?.data) {
        this.data = {
          adapters: response.data.adapters || [],
          prompts: response.data.prompts || [],
          tools: response.data.tools || [],
          skills: response.data.skills || [],
          tasks: response.data.tasks || [],
          mcp: response.data.mcp || { configured: 0, connected: 0, total_tools: 0 },
        };
      }
    } catch (error) {
      window.toastFrontendError?.(
        error?.message || "Failed to load resource hub",
        "Resource Hub"
      );
    } finally {
      this.isLoading = false;
    }
  },

  async openSection(section) {
    this.activeSection = section;
    this.preview = { kind: "", name: "", content: "" };
  },

  async previewItem(name) {
    if (!name || this.activeSection === "overview" || this.activeSection === "tasks") return;
    try {
      const response = await callJsonApi("/resource_file", {
        kind: this.activeSection,
        name,
      });
      if (response?.ok) {
        this.preview = {
          kind: this.activeSection,
          name,
          content: response.content || "",
        };
      }
    } catch (error) {
      window.toastFrontendError?.(
        error?.message || "Failed to load file",
        "Resource Hub"
      );
    }
  },

  openSkillsSettings() {
    window.closeModal("modals/resource-hub/resource-hub-modal.html");
    window.Alpine?.store("settings")?.open("skills");
  },

  openMcpSettings() {
    window.closeModal("modals/resource-hub/resource-hub-modal.html");
    window.Alpine?.store("settings")?.open("mcp");
  },

  openScheduler() {
    window.closeModal("modals/resource-hub/resource-hub-modal.html");
    window.openModal("modals/scheduler/scheduler-modal.html");
  },
};

export const store = createStore("resourceHubStore", model);

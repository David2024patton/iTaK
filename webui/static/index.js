import * as msgs from "/js/messages.js";
import * as api from "/js/api.js";
import * as css from "/js/css.js";
import { sleep } from "/js/sleep.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { store as inputStore } from "/components/chat/input/input-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as tasksStore } from "/components/sidebar/tasks/tasks-store.js";
import { store as chatTopStore } from "/components/chat/top-section/chat-top-store.js";
import { store as _tooltipsStore } from "/components/tooltips/tooltip-store.js";
import { store as messageQueueStore } from "/components/chat/message-queue/message-queue-store.js";
import { store as syncStore } from "/components/sync/sync-store.js"
import { initInteractionLogger } from "/js/interaction-logger.js";

globalThis.fetchApi = api.fetchApi; // TODO - backward compatibility for non-modular scripts, remove once refactored to alpine

// Declare variables for DOM elements, they will be assigned on DOMContentLoaded
let leftPanel,
  rightPanel,
  container,
  chatInput,
  chatHistory,
  sendButton,
  inputSection,
  statusSection,
  progressBar,
  autoScrollSwitch,
  timeDate;

let autoScroll = true;
let context = null;
globalThis.resetCounter = 0; // Used by stores and getChatBasedId
let skipOneSpeech = false;
let sendInFlight = false;
const MESSAGE_SEND_TIMEOUT_MS = 120000;

// Sidebar toggle logic is now handled by sidebar-store.js

export async function sendMessage() {
  if (sendInFlight) {
    const message = inputStore.message.trim();
    const attachmentsWithUrls = attachmentsStore.getAttachmentsForSending();
    const hasAttachments = attachmentsWithUrls.length > 0;

    if (message || hasAttachments) {
      messageQueueStore.addToQueue(message, attachmentsWithUrls);
      inputStore.reset();
    }
    return;
  }

  sendInFlight = true;
  try {
    const message = inputStore.message.trim();
    const attachmentsWithUrls = attachmentsStore.getAttachmentsForSending();
    const hasAttachments = attachmentsWithUrls.length > 0;

    // If empty input but has queued messages, send all queued
    if (!message && !hasAttachments && messageQueueStore.hasQueue) {
      await messageQueueStore.sendAll();
      return;
    }

    if (message || hasAttachments) {
      // Check if agent is busy - queue instead of sending
      if (chatsStore.selectedContext?.running || messageQueueStore.hasQueue) {
        const success = messageQueueStore.addToQueue(message, attachmentsWithUrls);
        // no await for the queue
        // if (success) {
        inputStore.reset();
        // }
        return;
      }

      // Sending a message is an explicit user intent to go to the bottom
      msgs.scrollOnNextProcessGroup();
      forceScrollChatToBottom();

      let response;
      const messageId = generateGUID();

      // Clear input and attachments
      inputStore.reset();

      // Include attachments in the user message
      if (hasAttachments) {
        const heading =
          attachmentsWithUrls.length > 0
            ? "Uploading attachments..."
            : "";

        // Render user message with attachments
        setMessages([{
          id: messageId, type: "user", heading, content: message, kvps: {
            // attachments: attachmentsWithUrls, // skip here, let the backend properly log them
          }
        }]);

        // sleep one frame to render the message before upload starts - better UX
        sleep(0);

        const formData = new FormData();
        formData.append("text", message);
        formData.append("context", context);
        formData.append("message_id", messageId);

        for (let i = 0; i < attachmentsWithUrls.length; i++) {
          formData.append("attachments", attachmentsWithUrls[i].file);
        }

        response = await api.fetchApi("/message_async", {
          method: "POST",
          timeoutMs: MESSAGE_SEND_TIMEOUT_MS,
          body: formData,
        });
      } else {
        // For text-only messages
        setMessages([
          {
            id: messageId,
            type: "user",
            content: message,
          },
        ]);

        const data = {
          text: message,
          context,
          message_id: messageId,
        };
        response = await api.fetchApi("/message_async", {
          method: "POST",
          timeoutMs: MESSAGE_SEND_TIMEOUT_MS,
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      }

      if (!response || !response.ok) {
        const errorBody = response ? await response.text() : "No response";
        throw new Error(errorBody || "message_async request failed");
      }

      // Handle response
      const jsonResponse = await response.json();
      if (!jsonResponse) {
        toast("No response returned.", "error");
      } else {
        setContext(jsonResponse.context);
        // Immediately request a fresh websocket snapshot for the active context.
        // This keeps UX snappy without HTTP polling fallback.
        try {
          if (typeof syncStore.sendStateRequest === "function") {
            await syncStore.sendStateRequest({ forceFull: true });
          }
        } catch (_error) {
          // Handshake/reconnect retries are handled by syncStore.
        }
      }
    }
  } catch (e) {
    toastFetchError("Error sending message", e); // Will use new notification system
  } finally {
    sendInFlight = false;
  }
}
globalThis.sendMessage = sendMessage;

function getChatHistoryEl() {
  return document.getElementById("chat-history");
}

function forceScrollChatToBottom() {
  const chatHistoryEl = getChatHistoryEl();
  if (!chatHistoryEl) return;
  chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}
globalThis.forceScrollChatToBottom = forceScrollChatToBottom;

export function toastFetchError(text, error) {
  console.error(text, error);
  // Use new frontend error notification system (async, but we don't need to wait)
  const errorMessage = error?.message || error?.toString() || "Unknown error";

  if (getConnectionStatus()) {
    // Backend is connected, just show the error
    toastFrontendError(`${text}: ${errorMessage}`).catch((e) =>
      console.error("Failed to show error toast:", e)
    );
  } else {
    // Backend is disconnected, show connection error
    toastFrontendError(
      `${text} (backend appears to be disconnected): ${errorMessage}`,
      "Connection Error"
    ).catch((e) => console.error("Failed to show connection error toast:", e));
  }
}
globalThis.toastFetchError = toastFetchError;

// Event listeners will be set up in DOMContentLoaded

export function updateChatInput(text) {
  const chatInputEl = document.getElementById("chat-input");
  if (!chatInputEl) {
    console.warn("`chatInput` element not found, cannot update.");
    return;
  }
  console.log("updateChatInput called with:", text);

  // Append text with proper spacing
  const currentValue = chatInputEl.value;
  const needsSpace = currentValue.length > 0 && !currentValue.endsWith(" ");
  chatInputEl.value = currentValue + (needsSpace ? " " : "") + text + " ";

  // Adjust height and trigger input event
  adjustTextareaHeight();
  chatInputEl.dispatchEvent(new Event("input"));

  console.log("Updated chat input value:", chatInputEl.value);
}

async function updateUserTime() {
  let userTimeElement = document.getElementById("time-date");

  while (!userTimeElement) {
    await sleep(100);
    userTimeElement = document.getElementById("time-date");
  }

  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();
  const ampm = hours >= 12 ? "pm" : "am";
  const formattedHours = hours % 12 || 12;

  // Format the time
  const timeString = `${formattedHours}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")} ${ampm}`;

  // Format the date
  const options = { year: "numeric", month: "short", day: "numeric" };
  const dateString = now.toLocaleDateString(undefined, options);

  // Update the HTML
  userTimeElement.innerHTML = `${timeString}<br><span id="user-date">${dateString}</span>`;
}

updateUserTime();
setInterval(updateUserTime, 1000);

async function setMessages(...params) {
  return await msgs.setMessages(...params);
}

globalThis.loadKnowledge = async function () {
  await inputStore.loadKnowledge();
};

function adjustTextareaHeight() {
  const chatInputEl = document.getElementById("chat-input");
  if (chatInputEl) {
    chatInputEl.style.height = "auto";
    chatInputEl.style.height = chatInputEl.scrollHeight + "px";
  }
}

export const sendJsonData = async function (url, data, options = {}) {
  return await api.callJsonApi(url, data, options);
  // const response = await api.fetchApi(url, {
  //     method: 'POST',
  //     headers: {
  //         'Content-Type': 'application/json'
  //     },
  //     body: JSON.stringify(data)
  // });

  // if (!response.ok) {
  //     const error = await response.text();
  //     throw new Error(error);
  // }
  // const jsonResponse = await response.json();
  // return jsonResponse;
};
globalThis.sendJsonData = sendJsonData;

function generateGUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0;
    var v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getConnectionStatus() {
  return chatTopStore.connected;
}
globalThis.getConnectionStatus = getConnectionStatus;

function setConnectionStatus(connected) {
  chatTopStore.connected = connected;
  // connectionStatus = connected;
  // // Broadcast connection status without touching Alpine directly
  // try {
  //   window.dispatchEvent(
  //     new CustomEvent("connection-status", { detail: { connected } })
  //   );
  // } catch (_e) {
  //   // no-op
  // }
}

let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;
let lastContextsSignature = "";
let lastTasksSignature = "";

function buildContextsSignature(contexts) {
  if (!Array.isArray(contexts) || contexts.length === 0) return "";
  let signature = `${contexts.length}|`;
  for (let i = 0; i < contexts.length; i++) {
    const ctx = contexts[i] || {};
    signature += `${ctx.id || ""}:${ctx.no || 0}:${ctx.created_at || 0}:${ctx.running ? 1 : 0}:${ctx.name || ""}:${ctx.project || ""};`;
  }
  return signature;
}

function buildTasksSignature(tasks) {
  if (!Array.isArray(tasks) || tasks.length === 0) return "";
  let signature = `${tasks.length}|`;
  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i] || {};
    signature += `${task.id || ""}:${task.no || 0}:${task.created_at || 0}:${task.running ? 1 : 0}:${task.state || ""}:${task.task_name || ""};`;
  }
  return signature;
}

export function buildStateRequestPayload(options = {}) {
  const { forceFull = false } = options || {};
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return {
    context: context || null,
    log_from: forceFull ? 0 : lastLogVersion,
    notifications_from: forceFull ? 0 : notificationStore.lastNotificationVersion || 0,
    timezone,
  };
}

export async function applySnapshot(snapshot, options = {}) {
  const { touchConnectionStatus = false, onLogGuidReset = null } = options || {};

  let updated = false;

  // Check if the snapshot is valid
  if (!snapshot || typeof snapshot !== "object") {
    console.error("Invalid snapshot payload");
    return { updated: false };
  }

  // deselect chat if it is requested by the backend
  if (snapshot.deselect_chat) {
    chatsStore.deselectChat();
    return { updated: false };
  }

  if (
    snapshot.context != context &&
    context !== null
  ) {
    return { updated: false };
  }

  // If the chat has been reset, reset cursors and request a resync from the caller.
  // Note: on first snapshot after a context switch, lastLogGuid is intentionally empty,
  // so the mismatch is expected and should not trigger a second state_request.
  if (lastLogGuid != snapshot.log_guid) {
    if (lastLogGuid) {
      const chatHistoryEl = document.getElementById("chat-history");
      if (chatHistoryEl) chatHistoryEl.innerHTML = "";
      lastLogVersion = 0;
      lastLogGuid = snapshot.log_guid;
      if (typeof onLogGuidReset === "function") {
        await onLogGuidReset();
      }
      return { updated: false, resynced: true };
    }
    // First guid observed for this context: accept it and continue applying snapshot.
    lastLogVersion = 0;
    lastLogGuid = snapshot.log_guid;
  }

  if (lastLogVersion != snapshot.log_version) {
    updated = true;
    await setMessages(snapshot.logs);
    afterMessagesUpdate(snapshot.logs);
  }

  lastLogVersion = snapshot.log_version;
  lastLogGuid = snapshot.log_guid;

  updateProgress(snapshot.log_progress, snapshot.log_progress_active);

  // Update notifications from snapshot
  notificationStore.updateFromPoll(snapshot);

  // set ui model vars from backend
  inputStore.paused = snapshot.paused;

  // Optional: treat snapshot application as proof of connectivity (poll path)
  if (touchConnectionStatus) {
    setConnectionStatus(true);
  }

  // Update chats/tasks only when payload actually changed to avoid unnecessary
  // Alpine reactivity churn during frequent state pushes.
  let contexts = Array.isArray(snapshot.contexts) ? snapshot.contexts : [];
  const contextsSignature = buildContextsSignature(contexts);
  if (contextsSignature !== lastContextsSignature) {
    chatsStore.applyContexts(contexts);
    lastContextsSignature = contextsSignature;
  }

  let tasks = Array.isArray(snapshot.tasks) ? snapshot.tasks : [];
  const tasksSignature = buildTasksSignature(tasks);
  if (tasksSignature !== lastTasksSignature) {
    tasksStore.applyTasks(tasks);
    lastTasksSignature = tasksSignature;
  }

  // Make sure the active context is properly selected in both lists
  if (context) {
    // Update selection in both stores
    chatsStore.setSelected(context);

    const contextInChats = chatsStore.contains(context);
    const contextInTasks = tasksStore.contains(context);

    if (contextInTasks) {
      tasksStore.setSelected(context);
    }

    if (!contextInChats && !contextInTasks) {
      if (chatsStore.contexts.length > 0) {
        // If it doesn't exist in the list but other contexts do, fall back to the first
        const firstChatId = chatsStore.firstId();
        if (firstChatId) {
          setContext(firstChatId);
          chatsStore.setSelected(firstChatId);
        }
      } else if (typeof deselectChat === "function") {
        // No contexts remain – clear state so the welcome screen can surface
        deselectChat();
      }
    }
  } else {
    // No context selected: keep it that way so the welcome screen stays visible.
  }

  // update message queue
  messageQueueStore.updateFromPoll();

  return { updated };
}

function afterMessagesUpdate(logs) {
  if (preferencesStore.speech) speakMessages(logs);
}

function speakMessages(logs) {
  if (skipOneSpeech) {
    skipOneSpeech = false;
    return;
  }
  // log.no, log.type, log.heading, log.content
  for (let i = logs.length - 1; i >= 0; i--) {
    const log = logs[i];

    // if already spoken, end
    // if(log.no < lastSpokenNo) break;

    // finished response
    if (log.type == "response") {
      // lastSpokenNo = log.no;
      speechStore.speakStream(
        getChatBasedId(log.no),
        log.content,
        log.kvps?.finished
      );
      return;

      // finished LLM headline, not response
    } else if (
      log.type == "agent" &&
      log.kvps &&
      log.kvps.headline &&
      log.kvps.tool_args &&
      log.kvps.tool_name != "response"
    ) {
      // lastSpokenNo = log.no;
      speechStore.speakStream(getChatBasedId(log.no), log.kvps.headline, true);
      return;
    }
  }
}

function updateProgress(progress, active) {
  const progressBarEl = document.getElementById("progress-bar");
  if (!progressBarEl) return;
  if (!progress) progress = "";

  setProgressBarShine(progressBarEl, active);

  progress = msgs.convertIcons(progress);

  if (progressBarEl.innerHTML != progress) {
    progressBarEl.innerHTML = progress;
  }
}

function setProgressBarShine(progressBarEl, active) {
  if (!progressBarEl) return;
  if (!active) {
    removeClassFromElement(progressBarEl, "shiny-text");
  } else {
    addClassToElement(progressBarEl, "shiny-text");
  }
}

globalThis.pauseAgent = async function (paused) {
  await inputStore.pauseAgent(paused);
};

function generateShortId() {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export const newContext = function () {
  context = generateShortId();
  setContext(context);
};
globalThis.newContext = newContext;

export const setContext = function (id) {
  if (id == context) return;
  context = id;
  // Always reset the log tracking variables when switching contexts
  // This ensures we get fresh data from the backend
  lastLogGuid = "";
  lastLogVersion = 0;
  lastSpokenNo = 0;

  // Stop speech when switching chats
  speechStore.stopAudio();

  // Clear the chat history immediately to avoid showing stale content
  const chatHistoryEl = document.getElementById("chat-history");
  if (chatHistoryEl) chatHistoryEl.innerHTML = "";

  // Update both selected states using stores
  chatsStore.setSelected(id);
  tasksStore.setSelected(id);

  // Trigger a new WS handshake for the newly selected context (push-based sync).
  // This keeps the UI current over websocket state sync.
  try {
    if (typeof syncStore.sendStateRequest === "function") {
      syncStore.sendStateRequest({ forceFull: true }).catch((error) => {
        console.error("[index] syncStore.sendStateRequest failed:", error);
      });
    }
  } catch (_error) {
    // no-op: sync store may not be initialized yet
  }

  //skip one speech if enabled when switching context
  if (preferencesStore.speech) skipOneSpeech = true;
};

export const deselectChat = function () {
  // Clear current context to show welcome screen
  setContext(null);

  // Clear selections so we don't auto-restore
  sessionStorage.removeItem("lastSelectedChat");
  sessionStorage.removeItem("lastSelectedTask");

  // Clear the chat history
  chatHistory.innerHTML = "";
};
globalThis.deselectChat = deselectChat;

export const getContext = function () {
  return context;
};
globalThis.getContext = getContext;
globalThis.setContext = setContext;

export const getChatBasedId = function (id) {
  return context + "-" + globalThis.resetCounter + "-" + id;
};

function addClassToElement(element, className) {
  element.classList.add(className);
}

function removeClassFromElement(element, className) {
  element.classList.remove(className);
}

export function justToast(text, type = "info", timeout = 5000, group = "") {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000, group);
}
globalThis.justToast = justToast;

export function toast(text, type = "info", timeout = 5000) {
  // Convert timeout from milliseconds to seconds for new notification system
  const display_time = Math.max(timeout / 1000, 1); // Minimum 1 second

  // Use new frontend notification system based on type
  switch (type.toLowerCase()) {
    case "error":
      return notificationStore.frontendError(text, "Error", display_time);
    case "success":
      return notificationStore.frontendInfo(text, "Success", display_time);
    case "warning":
      return notificationStore.frontendWarning(text, "Warning", display_time);
    case "info":
    default:
      return notificationStore.frontendInfo(text, "Info", display_time);
  }
}
globalThis.toast = toast;


import { store as _chatNavigationStore } from "/components/chat/navigation/chat-navigation-store.js";


// Navigation logic in chat-navigation-store.js
// forceScrollChatToBottom is kept here as it is used by system events


// setInterval(poll, 250);

async function startPolling() {
  if (typeof syncStore?.init === "function") {
    await syncStore.init();
  }
}

// All initializations and event listeners are now consolidated here
document.addEventListener("DOMContentLoaded", function () {
  initInteractionLogger();

  // Assign DOM elements to variables now that the DOM is ready
  leftPanel = document.getElementById("left-panel");
  rightPanel = document.getElementById("right-panel");
  container = document.querySelector(".container");
  chatInput = document.getElementById("chat-input");
  chatHistory = document.getElementById("chat-history");
  sendButton = document.getElementById("send-button");
  inputSection = document.getElementById("input-section");
  statusSection = document.getElementById("status-section");
  progressBar = document.getElementById("progress-bar");
  autoScrollSwitch = document.getElementById("auto-scroll-switch");
  timeDate = document.getElementById("time-date-container");


  // Start websocket state synchronization
  startPolling();
});

/*
 * A0 Chat UI
 *
 * Unified sidebar layout:
 * - Both Chats and Tasks lists are always visible in a vertical layout
 * - Both lists are sorted by creation time (newest first)
 * - Tasks use the same context system as chats for communication with the backend
 */

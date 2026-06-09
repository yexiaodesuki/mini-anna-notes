import { getRuntime } from "./runtime.js";

import {
    loadNotes,
    addNote,
    deleteNote
} from "./notesStore.js";

import {
    summarizeNotes
} from "./summarizeService.js";

import {
    renderNotes,
    setSummary
} from "./ui.js";

async function refreshNotes() {
    const notes = await loadNotes();

    renderNotes(notes);
}

async function handleSave() {

    const input = document.getElementById("inputNote");

    const content = input.value.trim();

    if (!content) return;

    await addNote(content);

    input.value = "";

    await refreshNotes();
}

async function handleSummarize() {

    try {

        setSummary("Summarizing...");

        const summary = await summarizeNotes();

        setSummary(summary);

    } catch (e) {

        setSummary("Error: " + e.message);

    }
}

async function init() {

    try {

        await getRuntime();

        await refreshNotes();

        // 保存按钮
        document.getElementById("saveBtn")
            .onclick = handleSave;

        // 总结按钮
        document.getElementById("summaryBtn")
            .onclick = handleSummarize;

        // ⭐ 只绑定一次（事件委托）
        document.getElementById("noteListBox").onclick = async (e) => {
            if (e.target.classList.contains("delete-btn")) {

                const id = Number(e.target.dataset.id);

                await deleteNote(id);

                await refreshNotes();
            }
        };

    } catch (e) {

        setSummary("Runtime not ready");

        console.error(e);

    }
}

init();
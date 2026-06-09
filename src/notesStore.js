import { getRuntime } from "./runtime.js";

const STORAGE_KEY = "notes";

export async function loadNotes() {
    const anna = await getRuntime();

    const res = await anna.storage.get({
        key: STORAGE_KEY
    });

    return res?.value || [];
}

export async function saveNotes(notes) {
    const anna = await getRuntime();

    await anna.storage.set({
        key: STORAGE_KEY,
        value: notes
    });
}

export async function addNote(content) {
    const notes = await loadNotes();

    notes.push({
        id: Date.now(),
        content,
        order: notes.length + 1,
        createAt: new Date().toLocaleString()
    });

    await saveNotes(notes);

    return notes;
}

export async function deleteNote(id) {
    const notes = await loadNotes();

    const filtered = notes.filter(n => n.id !== id);

    await saveNotes(filtered);

    return filtered;
}
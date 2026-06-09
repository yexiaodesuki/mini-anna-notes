import { getRuntime } from "./runtime.js";
import { loadNotes } from "./notesStore.js";

const TOOL_ID = "tool-dev-notes-summarizer";

export async function summarizeNotes() {
    const anna = await getRuntime();

    const notes = await loadNotes();

    const result = await anna.tools.invoke({
        tool_id: TOOL_ID,
        method: "invoke",
        args: {
            notes: notes.map(n => n.content)
        }
    });

    return result.summary;
}
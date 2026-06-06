import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const TOOL_ID = "tool-dev-notes-summarizer";

let anna;
let noteList = [];

// ---------- 初始化 Runtime ----------
async function init() {
    const summaryBox = document.getElementById("summary");

    try {
        anna = await AnnaAppRuntime.connect();
        console.log("Runtime connected");
    } catch (e) {
        summaryBox.innerText = "Standalone mode (no runtime)";
        return;
    }

    // UI绑定
    document.getElementById("saveBtn").onclick = saveNote;
    document.getElementById("summaryBtn").onclick = callSummarize;
}

// ---------- 保存笔记 ----------
function saveNote() {
    const input = document.getElementById("inputNote");
    const val = input.value.trim();
    if (!val) return;

    noteList.push({
        id: Date.now(),
        content: val,
        order: noteList.length + 1,
        createAt: new Date().toLocaleString()
    });

    input.value = "";
    renderList();
}

// ---------- 渲染列表 ----------
function renderList() {
    const box = document.getElementById("noteListBox");

    box.innerHTML = noteList.map(item => `
        <div class="item">
            <p>序号：${item.order}｜${item.createAt}</p>
            <p>内容：${item.content}</p>
        </div>
    `).join("");
}

// ---------- 调用 Tool ----------
async function callSummarize() {
    const summaryBox = document.getElementById("summary");

    if (!anna) {
        summaryBox.innerText = "Runtime not ready";
        return;
    }

    try {
        summaryBox.innerText = "Summarizing...";

        const res = await anna.tools.invoke({
            tool_id: "tool-dev-notes-summarizer",
            method: "invoke",
            args: {
                notes: noteList.map(n => n.content)
            }
        });

        summaryBox.innerText = res.summary;

    } catch (e) {
        summaryBox.innerText = "Error: " + e.message;
    }
}

// ---------- 启动 ----------
init();
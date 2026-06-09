export function renderNotes(notes) {
    const box = document.getElementById("noteListBox");

    if (!notes.length) {
        box.innerHTML = "<p>暂无笔记</p>";
        return;
    }

    box.innerHTML = notes.map(item => `
        <div class="item" data-id="${item.id}">
            <p>序号：${item.order}｜${item.createAt}</p>
            <p>内容：${item.content}</p>
            <button class="delete-btn" data-id="${item.id}">
                删除
            </button>
        </div>
    `).join("");
}

export function setSummary(text) {
    const box = document.getElementById("summary");

    if (!box) return;

    box.textContent = text;
}
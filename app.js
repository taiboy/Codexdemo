"use strict";

const form = document.querySelector("#task-form");
const input = document.querySelector("#task-input");
const list = document.querySelector("#task-list");
const summary = document.querySelector("#task-summary");
const emptyMessage = document.querySelector("#empty-message");
const error = document.querySelector("#input-error");

function updateSummary() {
  const total = list.children.length;
  const completed = list.querySelectorAll("input:checked").length;
  summary.textContent = `未完了 ${total - completed} 件 / 全 ${total} 件`;
  emptyMessage.hidden = total > 0;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) {
    error.textContent = "空白だけのタスクは追加できません。";
    input.focus();
    return;
  }
  error.textContent = "";

  const item = document.createElement("li");
  item.className = "task";
  const label = document.createElement("label");
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  const text = document.createElement("span");
  text.textContent = title;
  label.append(checkbox, text);

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.textContent = "削除";
  deleteButton.setAttribute("aria-label", `${title}を削除`);

  checkbox.addEventListener("change", () => {
    item.classList.toggle("completed", checkbox.checked);
    updateSummary();
  });
  deleteButton.addEventListener("click", () => {
    const nextFocus = item.nextElementSibling?.querySelector("button")
      ?? item.previousElementSibling?.querySelector("button")
      ?? input;
    item.remove();
    updateSummary();
    nextFocus.focus();
  });

  item.append(label, deleteButton);
  list.append(item);
  form.reset();
  updateSummary();
  input.focus();
});

input.addEventListener("input", () => {
  error.textContent = "";
});

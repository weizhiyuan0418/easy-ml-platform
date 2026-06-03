const state = {
  fields: [],
  records: [],
};

const roleLabels = { input: "输入", output: "输出" };
const typeLabels = { number: "数值", category: "类别", boolean: "布尔", datetime: "日期/时间" };

function csrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, {
    ...options,
    headers,
  });
  const data = await response.json();
  if (!response.ok || data.success === false) {
    throw new Error(data.error || `请求失败: ${response.status}`);
  }
  return data;
}

function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 2600);
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "是" : "否";
  return String(value);
}

function asJson(data) {
  return JSON.stringify(data, null, 2);
}

function switchTab(tab) {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  document.querySelectorAll(".tab-page").forEach((page) => {
    page.classList.toggle("active", page.id === `tab-${tab}`);
  });
}

function activeFields() {
  return state.fields.filter((field) => field.is_active);
}

async function refreshDashboard() {
  const data = await api("/api/dashboard/summary/");
  document.getElementById("projectName").textContent = data.project.name;
  const totals = data.totals;
  const kpis = [
    ["字段数", totals.field_count],
    ["输入字段", totals.input_count],
    ["输出字段", totals.output_count],
    ["数据记录", totals.record_count],
    ["模型运行", totals.model_run_count],
    ["启用模型", totals.active_model_count],
  ];
  document.getElementById("dashboardKpis").innerHTML = kpis
    .map(([label, value]) => `<div class="kpi"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
  document.getElementById("missingnessBody").innerHTML = data.missingness
    .map((row) => `
      <tr>
        <td>${row.label}<br><small>${row.field}</small></td>
        <td>${roleLabels[row.role] || row.role}</td>
        <td>${row.present_count}</td>
        <td>${row.missing_count}</td>
        <td>${(row.missing_ratio * 100).toFixed(1)}%</td>
      </tr>
    `)
    .join("");
}

async function refreshFields() {
  const data = await api("/api/fields/");
  state.fields = data.fields;
  document.getElementById("fieldsBody").innerHTML = data.fields
    .map((field) => `
      <tr>
        <td>${field.name}</td>
        <td>${field.label}</td>
        <td>${roleLabels[field.role]}</td>
        <td>${typeLabels[field.field_type]}</td>
        <td>${field.required ? "是" : "否"}</td>
        <td>${field.is_active ? "是" : "否"}</td>
        <td class="actions">
          <button class="secondary" data-edit-field="${field.id}">编辑</button>
          <button class="danger" data-delete-field="${field.id}">删除</button>
        </td>
      </tr>
    `)
    .join("");
  renderDynamicForms();
}

function resetFieldForm() {
  document.getElementById("fieldId").value = "";
  document.getElementById("fieldName").value = "";
  document.getElementById("fieldLabel").value = "";
  document.getElementById("fieldRole").value = "input";
  document.getElementById("fieldType").value = "number";
  document.getElementById("fieldUnit").value = "";
  document.getElementById("fieldSort").value = String(state.fields.length + 1);
  document.getElementById("fieldChoices").value = "";
  document.getElementById("fieldRequired").checked = false;
  document.getElementById("fieldActive").checked = true;
}

async function saveField(event) {
  event.preventDefault();
  const id = document.getElementById("fieldId").value;
  const payload = {
    name: document.getElementById("fieldName").value.trim(),
    label: document.getElementById("fieldLabel").value.trim(),
    role: document.getElementById("fieldRole").value,
    field_type: document.getElementById("fieldType").value,
    unit: document.getElementById("fieldUnit").value.trim(),
    sort_order: Number(document.getElementById("fieldSort").value || 1),
    choices: document.getElementById("fieldChoices").value.split(",").map((item) => item.trim()).filter(Boolean),
    required: document.getElementById("fieldRequired").checked,
    is_active: document.getElementById("fieldActive").checked,
  };
  await api(id ? `/api/fields/${id}/` : "/api/fields/", {
    method: id ? "PATCH" : "POST",
    body: JSON.stringify(payload),
  });
  resetFieldForm();
  await refreshAll();
  toast("字段已保存");
}

function editField(id) {
  const field = state.fields.find((item) => item.id === Number(id));
  if (!field) return;
  document.getElementById("fieldId").value = field.id;
  document.getElementById("fieldName").value = field.name;
  document.getElementById("fieldLabel").value = field.label;
  document.getElementById("fieldRole").value = field.role;
  document.getElementById("fieldType").value = field.field_type;
  document.getElementById("fieldUnit").value = field.unit || "";
  document.getElementById("fieldSort").value = field.sort_order;
  document.getElementById("fieldChoices").value = (field.choices || []).join(",");
  document.getElementById("fieldRequired").checked = field.required;
  document.getElementById("fieldActive").checked = field.is_active;
  switchTab("fields");
}

async function deleteField(id) {
  if (!confirm("确认删除这个字段？数据记录中的同名值不会自动清理，但该字段不再用于表单和训练。")) return;
  await api(`/api/fields/${id}/`, { method: "DELETE" });
  await refreshAll();
  toast("字段已删除");
}

function inputForField(field, prefix, value = "") {
  const id = `${prefix}-${field.name}`;
  if (field.field_type === "boolean") {
    return `
      <label>${field.label}
        <select id="${id}" data-field="${field.name}">
          <option value="">请选择</option>
          <option value="true" ${value === true ? "selected" : ""}>是</option>
          <option value="false" ${value === false ? "selected" : ""}>否</option>
        </select>
      </label>`;
  }
  if (field.field_type === "category" && field.choices && field.choices.length) {
    return `
      <label>${field.label}
        <select id="${id}" data-field="${field.name}">
          <option value="">请选择</option>
          ${field.choices.map((choice) => `<option value="${choice}" ${choice === value ? "selected" : ""}>${choice}</option>`).join("")}
        </select>
      </label>`;
  }
  const type = field.field_type === "number" ? "number" : field.field_type === "datetime" ? "datetime-local" : "text";
  const step = field.field_type === "number" ? ' step="any"' : "";
  return `<label>${field.label}<input id="${id}" data-field="${field.name}" type="${type}"${step} value="${valueText(value) === "-" ? "" : valueText(value)}"></label>`;
}

function renderDynamicForms() {
  const fields = activeFields();
  const recordFields = fields;
  const predictFields = fields.filter((field) => field.role === "input");
  document.getElementById("recordInputs").innerHTML = recordFields.map((field) => inputForField(field, "record")).join("");
  document.getElementById("predictInputs").innerHTML = predictFields.map((field) => inputForField(field, "predict")).join("");
}

function collectValues(prefix, fields) {
  const values = {};
  for (const field of fields) {
    const el = document.getElementById(`${prefix}-${field.name}`);
    if (!el) continue;
    values[field.name] = el.value;
  }
  return values;
}

function resetRecordForm() {
  document.getElementById("recordId").value = "";
  renderDynamicForms();
}

async function saveRecord(event) {
  event.preventDefault();
  const id = document.getElementById("recordId").value;
  const values = collectValues("record", activeFields());
  await api(id ? `/api/records/${id}/` : "/api/records/", {
    method: id ? "PATCH" : "POST",
    body: JSON.stringify(values),
  });
  resetRecordForm();
  await refreshAll();
  toast("数据已保存");
}

async function refreshRecords() {
  const data = await api("/api/records/");
  state.records = data.records;
  const fields = activeFields();
  document.getElementById("recordsHead").innerHTML = `
    <tr>
      <th>ID</th>
      ${fields.map((field) => `<th>${field.label}<br><small>${field.name}</small></th>`).join("")}
      <th>操作</th>
    </tr>`;
  document.getElementById("recordsBody").innerHTML = data.records
    .map((record) => `
      <tr>
        <td>${record.id}</td>
        ${fields.map((field) => `<td>${valueText(record.values[field.name])}</td>`).join("")}
        <td class="actions">
          <button class="secondary" data-edit-record="${record.id}">编辑</button>
          <button class="danger" data-delete-record="${record.id}">删除</button>
        </td>
      </tr>
    `)
    .join("");
}

function editRecord(id) {
  const record = state.records.find((item) => item.id === Number(id));
  if (!record) return;
  document.getElementById("recordId").value = record.id;
  for (const field of activeFields()) {
    const el = document.getElementById(`record-${field.name}`);
    if (el) el.value = record.values[field.name] ?? "";
  }
  switchTab("records");
}

async function deleteRecord(id) {
  if (!confirm("确认删除这条数据？")) return;
  await api(`/api/records/${id}/`, { method: "DELETE" });
  await refreshAll();
  toast("数据已删除");
}

function importFormData() {
  const file = document.getElementById("importFile").files[0];
  if (!file) throw new Error("请选择 CSV 或 Excel 文件");
  const formData = new FormData();
  formData.append("file", file);
  return formData;
}

async function runImport(path) {
  const data = await api(path, { method: "POST", body: importFormData() });
  document.getElementById("importOutput").textContent = asJson(data);
  await refreshAll();
}

async function refreshModels() {
  const data = await api("/api/models/summary/");
  document.getElementById("modelsList").innerHTML = data.targets
    .map((target) => `
      <div class="model-card">
        <h4>${target.target.label} <small>${target.target.name}</small></h4>
        <p>任务类型：${target.task_type === "regression" ? "回归" : "分类"}</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>模型</th>
                <th>指标</th>
                <th>样本</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${target.runs.map((run) => `
                <tr>
                  <td>${run.candidate_label}</td>
                  <td>${run.error_message ? run.error_message : asJson(run.metrics)}</td>
                  <td>${run.training_sample_count}</td>
                  <td>
                    ${run.is_active ? '<span class="pill active">已启用</span>' : ""}
                    ${run.is_recommended ? '<span class="pill recommended">推荐</span>' : ""}
                  </td>
                  <td>${run.error_message ? "-" : `<button class="secondary" data-activate-model="${run.id}">启用</button>`}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `)
    .join("");
}

async function trainModels() {
  document.getElementById("modelsList").innerHTML = '<div class="model-card">训练中，请稍候...</div>';
  const data = await api("/api/train/", { method: "POST", body: JSON.stringify({}) });
  await refreshModels();
  await refreshDashboard();
  toast("训练完成");
  console.log(data);
}

async function activateModel(id) {
  await api("/api/models/activate/", { method: "POST", body: JSON.stringify({ model_run_id: Number(id) }) });
  await refreshModels();
  await refreshDashboard();
  toast("模型已启用");
}

async function runPredict(event) {
  event.preventDefault();
  const fields = activeFields().filter((field) => field.role === "input");
  const payload = collectValues("predict", fields);
  const data = await api("/api/predict/", { method: "POST", body: JSON.stringify(payload) });
  document.getElementById("predictOutput").textContent = asJson(data.results);
}

async function refreshAll() {
  await refreshFields();
  await refreshRecords();
  await refreshDashboard();
  await refreshModels();
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  if (target.matches(".nav-button")) switchTab(target.dataset.tab);
  if (target.dataset.editField) editField(target.dataset.editField);
  if (target.dataset.deleteField) {
    try { await deleteField(target.dataset.deleteField); } catch (error) { toast(error.message); }
  }
  if (target.dataset.editRecord) editRecord(target.dataset.editRecord);
  if (target.dataset.deleteRecord) {
    try { await deleteRecord(target.dataset.deleteRecord); } catch (error) { toast(error.message); }
  }
  if (target.dataset.activateModel) {
    try { await activateModel(target.dataset.activateModel); } catch (error) { toast(error.message); }
  }
});

document.getElementById("fieldForm").addEventListener("submit", (event) => saveField(event).catch((error) => toast(error.message)));
document.getElementById("recordForm").addEventListener("submit", (event) => saveRecord(event).catch((error) => toast(error.message)));
document.getElementById("predictForm").addEventListener("submit", (event) => runPredict(event).catch((error) => toast(error.message)));
document.getElementById("resetFieldForm").addEventListener("click", resetFieldForm);
document.getElementById("resetRecordForm").addEventListener("click", resetRecordForm);
document.getElementById("refreshDashboard").addEventListener("click", () => refreshDashboard().catch((error) => toast(error.message)));
document.getElementById("refreshModels").addEventListener("click", () => refreshModels().catch((error) => toast(error.message)));
document.getElementById("trainModels").addEventListener("click", () => trainModels().catch((error) => toast(error.message)));
document.getElementById("previewImport").addEventListener("click", () => runImport("/api/import/preview/").catch((error) => toast(error.message)));
document.getElementById("commitImport").addEventListener("click", () => runImport("/api/import/commit/").catch((error) => toast(error.message)));

refreshAll().then(resetFieldForm).catch((error) => toast(error.message));

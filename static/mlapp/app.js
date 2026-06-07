const STORAGE_LANGUAGE_KEY = "easy_ml_platform_language";
const STORAGE_PROJECT_KEY = "easy_ml_platform_project_id";

const state = {
  fields: [],
  records: [],
  projects: [],
  currentProjectId: null,
  dashboard: null,
  lastImportResult: null,
  lastImportMode: "",
  lastPredictionResults: {},
  lastPredictionAction: "",
  lastTrainingResult: null,
  language: initialLanguage(),
};

const translations = {
  zh: {
    language: { label: "界面语言" },
    nav: { dashboard: "概览", fields: "字段", records: "数据", import: "导入", models: "模型", predict: "预测" },
    roles: { input: "输入", output: "输出" },
    types: { number: "数值", category: "类别", boolean: "布尔", datetime: "日期/时间" },
    taskTypes: { regression: "回归", classification: "分类" },
    boolean: { true: "是", false: "否" },
    actions: {
      refresh: "刷新",
      saveField: "保存字段",
      saveRecord: "保存数据",
      clear: "清空",
      exportCsv: "导出 CSV",
      downloadTemplate: "下载模板",
      previewImport: "预检",
      commitImport: "确认导入",
      trainAll: "训练全部输出",
      predict: "开始预测",
      createProject: "新建",
      loadSample: "加载示例项目",
      goFields: "配置字段",
      goRecords: "录入数据",
      goImport: "导入数据",
      goModels: "训练模型",
      goPredict: "去预测",
      edit: "编辑",
      delete: "删除",
      activate: "启用",
      cancel: "取消",
      confirm: "确认",
      close: "关闭",
      saving: "保存中...",
      importing: "导入中...",
      previewing: "预检中...",
      training: "训练中...",
      predicting: "预测中...",
    },
    dashboard: {
      title: "项目概览",
      subtitle: "查看字段、数据、模型和缺失值状态。",
      missingnessTitle: "字段缺失情况",
      emptyMissingness: "还没有可统计的字段。先在“字段”页配置输入和输出字段。",
      kpiFields: "字段数",
      kpiInputs: "输入字段",
      kpiOutputs: "输出字段",
      kpiRecords: "数据记录",
      kpiRuns: "模型运行",
      kpiActiveModels: "启用模型",
    },
    projects: {
      title: "项目",
      current: "当前项目",
      namePlaceholder: "新项目名称",
      created: "项目已创建",
      sampleCreated: "示例项目已创建",
    },
    onboarding: {
      title: "快速开始",
      complete: "已完成",
      current: "当前步骤",
      pending: "待完成",
      fieldsTitle: "配置字段",
      fieldsDesc: "创建至少一个输入字段和一个输出字段，或直接加载示例项目。",
      recordsTitle: "添加数据",
      recordsDesc: "手动录入记录，或导入 CSV/Excel 数据。",
      trainTitle: "训练模型",
      trainDesc: "系统会为每个输出字段训练候选模型并启用推荐模型。",
      predictTitle: "开始预测",
      predictDesc: "输入新样本，查看所有已启用输出模型的预测结果。",
    },
    fields: {
      title: "字段配置",
      subtitle: "配置输入和输出字段，字段名用于 API、导入导出和模型训练。",
      listTitle: "字段列表",
      name: "字段名",
      label: "显示名",
      role: "角色",
      type: "类型",
      unit: "单位",
      sort: "排序",
      choices: "候选值",
      required: "必填",
      active: "启用",
      namePlaceholder: "density",
      labelPlaceholder: "密度",
      optionalPlaceholder: "可空",
      choicesPlaceholder: "类别A,类别B",
      empty: "还没有字段。先创建至少一个输入字段和一个输出字段。",
      saved: "字段已保存",
      deleted: "字段已删除",
      confirmDeleteTitle: "删除字段",
      confirmDelete: "确认删除“{name}”？数据记录中的同名值不会自动清理，但该字段不再用于表单和训练。",
    },
    records: {
      title: "数据集",
      subtitle: "按当前字段配置动态录入和维护数据。",
      listTitle: "记录列表",
      emptyFields: "请先配置字段，数据表单会按字段自动生成。",
      emptyRecords: "还没有数据。你可以手动录入，或在“导入”页上传 CSV/Excel。",
      saved: "数据已保存",
      deleted: "数据已删除",
      confirmDeleteTitle: "删除数据",
      confirmDelete: "确认删除这条数据？该操作不可恢复。",
    },
    import: {
      title: "导入数据",
      subtitle: "支持 UTF-8/UTF-8-SIG CSV 和 Excel，列名必须匹配字段名。",
      chooseFile: "请选择 CSV 或 Excel 文件",
      previewPassed: "预检通过",
      previewFailed: "预检发现问题",
      commitSuccess: "导入完成",
      commitFailed: "导入失败",
      summary: "列数 {columns}，有效行 {valid}，错误 {errors}",
      matchedColumns: "已匹配列：{count}",
      missingColumns: "缺少必填列：{columns}",
      unknownColumns: "未知列：{columns}",
      imported: "已导入 {count} 条记录。",
      noErrors: "没有发现格式错误。",
      errorsTitle: "错误列表",
      raw: "查看原始响应",
    },
    models: {
      title: "模型训练与选择",
      subtitle: "每个输出目标分别训练候选模型，并按指标自动推荐，用户也可手动启用。",
      statusTitle: "模型状态",
      empty: "还没有输出字段。请先在“字段”页创建输出字段。",
      noRuns: "这个输出目标还没有训练结果。",
      taskType: "任务类型",
      model: "模型",
      metrics: "指标",
      samples: "样本",
      status: "状态",
      active: "已启用",
      recommended: "推荐",
      failed: "训练失败",
      trained: "训练完成",
      trainingPartial: "部分目标训练完成",
      trainingFailed: "训练未完成",
      targetFailed: "该输出目标训练失败",
      nextStep: "下一步建议",
      needMoreRows: "请补充更多带目标值的数据后重新训练。",
      activated: "模型已启用",
    },
    predict: {
      title: "预测",
      subtitle: "根据当前输入字段动态生成表单，返回所有已启用输出模型的预测结果。",
      emptyInputs: "还没有输入字段。请先在“字段”页创建输入字段。",
      emptyResults: "预测结果会显示在这里。",
      noActiveAction: "当前项目还没有已启用模型，请先完成训练或在模型页启用一个模型。",
      resultTitle: "预测结果",
      prediction: "预测值",
      model: "使用模型",
      features: "输入特征",
      raw: "查看原始结果",
    },
    tables: {
      field: "字段",
      role: "角色",
      present: "已填写",
      missing: "缺失",
      missingRatio: "缺失率",
      actions: "操作",
      id: "ID",
    },
    toast: {
      requestFailed: "请求失败: {status}",
      unknownError: "操作失败，请检查输入后重试。",
    },
    errors: {
      project_name_required: "项目名称不能为空。",
      duplicate_project_name: "项目名称已存在，请换一个名称。",
      upload_required: "请先选择 CSV 或 Excel 文件。",
      field_required: "{field} 为必填项。",
      invalid_number: "{field} 必须是有效数值。",
      invalid_boolean: "{field} 必须是布尔值。",
      invalid_datetime: "{field} 必须是合法日期/时间。",
      invalid_choice: "{field} 必须是候选值之一。",
      invalid_field_name: "字段名只能包含字母、数字、下划线，且不能以数字开头。",
      duplicate_field_name: "字段名已存在，请换一个字段名。",
      invalid_payload: "请求数据格式不正确。",
      field_validation_failed: "字段配置校验失败，请检查角色、类型和候选值。",
      missing_input_fields: "请先配置至少一个输入字段，再训练或预测。",
      missing_output_fields: "请先配置至少一个输出字段，再训练模型。",
      no_active_model: "当前项目没有已启用模型。请先训练模型，或在模型页启用一个模型。",
      not_enough_rows: "训练数据不足。每个输出目标至少需要 3 条带目标值的数据。",
      unknown_field: "包含未知字段或未知列，请检查字段配置和导入文件表头。",
      failed_model_activation: "不能启用训练失败的模型。",
    },
  },
  en: {
    language: { label: "Language" },
    nav: { dashboard: "Dashboard", fields: "Fields", records: "Data", import: "Import", models: "Models", predict: "Predict" },
    roles: { input: "Input", output: "Output" },
    types: { number: "Number", category: "Category", boolean: "Boolean", datetime: "Date/Time" },
    taskTypes: { regression: "Regression", classification: "Classification" },
    boolean: { true: "Yes", false: "No" },
    actions: {
      refresh: "Refresh",
      saveField: "Save Field",
      saveRecord: "Save Data",
      clear: "Clear",
      exportCsv: "Export CSV",
      downloadTemplate: "Download Template",
      previewImport: "Preview",
      commitImport: "Import",
      trainAll: "Train All Outputs",
      predict: "Predict",
      createProject: "Create",
      loadSample: "Load Sample Project",
      goFields: "Configure Fields",
      goRecords: "Enter Data",
      goImport: "Import Data",
      goModels: "Train Models",
      goPredict: "Go Predict",
      edit: "Edit",
      delete: "Delete",
      activate: "Activate",
      cancel: "Cancel",
      confirm: "Confirm",
      close: "Close",
      saving: "Saving...",
      importing: "Importing...",
      previewing: "Previewing...",
      training: "Training...",
      predicting: "Predicting...",
    },
    dashboard: {
      title: "Project Dashboard",
      subtitle: "Review fields, data, models, and missing values.",
      missingnessTitle: "Field Missingness",
      emptyMissingness: "No fields to summarize yet. Configure input and output fields first.",
      kpiFields: "Fields",
      kpiInputs: "Input Fields",
      kpiOutputs: "Output Fields",
      kpiRecords: "Records",
      kpiRuns: "Model Runs",
      kpiActiveModels: "Active Models",
    },
    projects: {
      title: "Projects",
      current: "Current Project",
      namePlaceholder: "New project name",
      created: "Project created",
      sampleCreated: "Sample project created",
    },
    onboarding: {
      title: "Quick Start",
      complete: "Done",
      current: "Current",
      pending: "Pending",
      fieldsTitle: "Configure Fields",
      fieldsDesc: "Create at least one input field and one output field, or load the sample project.",
      recordsTitle: "Add Data",
      recordsDesc: "Enter records manually or import CSV/Excel data.",
      trainTitle: "Train Models",
      trainDesc: "The app trains candidates for each output field and activates the recommended model.",
      predictTitle: "Run Predictions",
      predictDesc: "Enter a new sample and view predictions from all active output models.",
    },
    fields: {
      title: "Field Configuration",
      subtitle: "Configure input and output fields. Field names are used by APIs, import/export, and training.",
      listTitle: "Field List",
      name: "Field Name",
      label: "Display Name",
      role: "Role",
      type: "Type",
      unit: "Unit",
      sort: "Sort",
      choices: "Choices",
      required: "Required",
      active: "Active",
      namePlaceholder: "density",
      labelPlaceholder: "Density",
      optionalPlaceholder: "Optional",
      choicesPlaceholder: "Class A,Class B",
      empty: "No fields yet. Create at least one input field and one output field.",
      saved: "Field saved",
      deleted: "Field deleted",
      confirmDeleteTitle: "Delete Field",
      confirmDelete: "Delete \"{name}\"? Existing record values with this name will not be removed, but this field will no longer be used by forms or training.",
    },
    records: {
      title: "Dataset",
      subtitle: "Enter and maintain records based on the current field configuration.",
      listTitle: "Record List",
      emptyFields: "Configure fields first. The data form is generated from active fields.",
      emptyRecords: "No records yet. Enter data manually or import a CSV/Excel file.",
      saved: "Data saved",
      deleted: "Data deleted",
      confirmDeleteTitle: "Delete Record",
      confirmDelete: "Delete this record? This action cannot be undone.",
    },
    import: {
      title: "Import Data",
      subtitle: "Supports UTF-8/UTF-8-SIG CSV and Excel. Column names must match field names.",
      chooseFile: "Choose a CSV or Excel file first",
      previewPassed: "Preview passed",
      previewFailed: "Preview found issues",
      commitSuccess: "Import completed",
      commitFailed: "Import failed",
      summary: "{columns} columns, {valid} valid rows, {errors} errors",
      matchedColumns: "Matched columns: {count}",
      missingColumns: "Missing required columns: {columns}",
      unknownColumns: "Unknown columns: {columns}",
      imported: "Imported {count} records.",
      noErrors: "No format errors found.",
      errorsTitle: "Errors",
      raw: "View raw response",
    },
    models: {
      title: "Model Training and Selection",
      subtitle: "Each output target is trained separately. The best model is recommended automatically and can be overridden manually.",
      statusTitle: "Model Status",
      empty: "No output fields yet. Create an output field on the Fields page first.",
      noRuns: "This output target has no training runs yet.",
      taskType: "Task Type",
      model: "Model",
      metrics: "Metrics",
      samples: "Samples",
      status: "Status",
      active: "Active",
      recommended: "Recommended",
      failed: "Failed",
      trained: "Training completed",
      trainingPartial: "Some targets trained",
      trainingFailed: "Training did not complete",
      targetFailed: "This output target failed to train",
      nextStep: "Next step",
      needMoreRows: "Add more records with target values, then train again.",
      activated: "Model activated",
    },
    predict: {
      title: "Predict",
      subtitle: "Generate an input form from current input fields and return predictions from all active output models.",
      emptyInputs: "No input fields yet. Create input fields on the Fields page first.",
      emptyResults: "Prediction results will appear here.",
      noActiveAction: "This project has no active model yet. Train models or activate one on the Models page first.",
      resultTitle: "Prediction Result",
      prediction: "Prediction",
      model: "Model",
      features: "Input Features",
      raw: "View raw result",
    },
    tables: {
      field: "Field",
      role: "Role",
      present: "Present",
      missing: "Missing",
      missingRatio: "Missing Ratio",
      actions: "Actions",
      id: "ID",
    },
    toast: {
      requestFailed: "Request failed: {status}",
      unknownError: "Operation failed. Check your input and try again.",
    },
    errors: {
      project_name_required: "Project name is required.",
      duplicate_project_name: "This project name already exists. Use a different name.",
      upload_required: "Choose a CSV or Excel file first.",
      field_required: "{field} is required.",
      invalid_number: "{field} must be a valid number.",
      invalid_boolean: "{field} must be a boolean value.",
      invalid_datetime: "{field} must be a valid date/time.",
      invalid_choice: "{field} must be one of the configured choices.",
      invalid_field_name: "Field names may only contain letters, numbers, and underscores, and cannot start with a number.",
      duplicate_field_name: "This field name already exists. Use a different field name.",
      invalid_payload: "The request payload is not valid.",
      field_validation_failed: "Field validation failed. Check role, type, and choices.",
      missing_input_fields: "Configure at least one input field before training or predicting.",
      missing_output_fields: "Configure at least one output field before training models.",
      no_active_model: "No active model exists for this project. Train models or activate a model on the Models page first.",
      not_enough_rows: "Not enough training data. Each output target needs at least 3 records with target values.",
      unknown_field: "Unknown field or column found. Check your field configuration and import headers.",
      failed_model_activation: "A failed training run cannot be activated.",
    },
  },
};

class ApiError extends Error {
  constructor(message, code, params = {}, status = 400) {
    super(message);
    this.name = "ApiError";
    this.code = code || "";
    this.params = params || {};
    this.status = status;
  }
}

function initialLanguage() {
  const saved = localStorage.getItem(STORAGE_LANGUAGE_KEY);
  if (saved === "zh" || saved === "en") return saved;
  return (navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en";
}

function t(key, params = {}) {
  const parts = key.split(".");
  let value = translations[state.language];
  for (const part of parts) value = value?.[part];
  if (typeof value !== "string") {
    value = translations.en;
    for (const part of parts) value = value?.[part];
  }
  const template = typeof value === "string" ? value : key;
  return template.replace(/\{(\w+)\}/g, (_match, name) => String(params[name] ?? ""));
}

function applyI18n() {
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  document.getElementById("languageSelect").value = state.language;
}

function setLanguage(language) {
  state.language = language === "zh" ? "zh" : "en";
  localStorage.setItem(STORAGE_LANGUAGE_KEY, state.language);
  applyI18n();
  renderProjects();
  renderDynamicForms();
  if (state.dashboard) renderOnboarding(state.dashboard.totals);
  if (state.lastImportResult) renderImportResult(state.lastImportResult, state.lastImportMode);
  if (state.lastPredictionAction) {
    renderPredictionAction(t("predict.noActiveAction"));
  } else {
    renderPredictionResults(state.lastPredictionResults);
  }
  refreshAll().catch((error) => toast(localizeError(error), "error"));
}

function csrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

function projectlessPath(path) {
  return path.startsWith("/api/projects/") || path.startsWith("/api/examples/");
}

function projectAwarePath(path) {
  if (!state.currentProjectId || projectlessPath(path)) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}project_id=${encodeURIComponent(state.currentProjectId)}`;
}

function updateProjectLinks() {
  const suffix = state.currentProjectId ? `?project_id=${encodeURIComponent(state.currentProjectId)}` : "";
  document.getElementById("exportCsvLink").href = `/api/export/csv/${suffix}`;
  document.getElementById("downloadTemplate").href = `/api/export/template/csv/${suffix}`;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = csrfToken();
  if (token) headers["X-CSRFToken"] = token;
  const response = await fetch(projectAwarePath(path), {
    ...options,
    headers,
  });
  let data = {};
  try {
    data = await response.json();
  } catch (_error) {
    data = {};
  }
  if (!response.ok || (data.success === false && !options.allowFailure)) {
    throw new ApiError(data.error || t("toast.requestFailed", { status: response.status }), data.error_code, data.error_params, response.status);
  }
  return data;
}

function localizeError(error) {
  if (error instanceof ApiError && error.code) {
    return t(`errors.${error.code}`, { ...error.params, field: error.params?.field || "" });
  }
  return error?.message || t("toast.unknownError");
}

function localizeErrorPayload(payload = {}) {
  if (payload.error_code) {
    return t(`errors.${payload.error_code}`, { ...(payload.error_params || {}), field: payload.error_params?.field || "" });
  }
  return payload.error || t("toast.unknownError");
}

function toast(message, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = `toast show ${type}`;
  window.clearTimeout(el.dataset.timer);
  el.dataset.timer = window.setTimeout(() => {
    el.classList.remove("show");
  }, 3200);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? t("boolean.true") : t("boolean.false");
  return String(value);
}

function asJson(data) {
  return JSON.stringify(data, null, 2);
}

function setBusy(button, busy, labelKey) {
  if (!button) return;
  button.disabled = busy;
  button.classList.toggle("loading", busy);
  if (busy) {
    button.dataset.idleText = button.textContent;
    button.textContent = t(labelKey);
  } else if (button.dataset.idleText) {
    button.textContent = button.dataset.idleText;
    delete button.dataset.idleText;
    applyI18n();
  }
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

function fieldById(id) {
  return state.fields.find((item) => item.id === Number(id));
}

function emptyRow(message, colspan) {
  return `<tr><td colspan="${colspan}"><div class="empty-state">${escapeHtml(message)}</div></td></tr>`;
}

function emptyBlock(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function renderProjects() {
  const select = document.getElementById("projectSelect");
  select.innerHTML = state.projects
    .map((project) => `<option value="${project.id}" ${project.id === state.currentProjectId ? "selected" : ""}>${escapeHtml(project.name)}</option>`)
    .join("");
  const current = state.projects.find((project) => project.id === state.currentProjectId);
  document.getElementById("projectName").textContent = current?.name || "Default Project";
  updateProjectLinks();
}

async function refreshProjects(preferredProjectId = null) {
  const data = await api("/api/projects/");
  state.projects = data.projects || [];
  const saved = Number(localStorage.getItem(STORAGE_PROJECT_KEY));
  const candidate = Number(preferredProjectId || state.currentProjectId || saved || 0);
  const hasCandidate = state.projects.some((project) => project.id === candidate);
  state.currentProjectId = hasCandidate ? candidate : (state.projects[0]?.id || null);
  if (state.currentProjectId) localStorage.setItem(STORAGE_PROJECT_KEY, String(state.currentProjectId));
  renderProjects();
}

function clearTransientResults() {
  state.lastImportResult = null;
  state.lastImportMode = "";
  state.lastPredictionResults = {};
  state.lastPredictionAction = "";
  state.lastTrainingResult = null;
  document.getElementById("importOutput").innerHTML = "";
  renderPredictionResults({});
}

async function changeProject(projectId) {
  state.currentProjectId = Number(projectId);
  localStorage.setItem(STORAGE_PROJECT_KEY, String(state.currentProjectId));
  clearTransientResults();
  resetFieldForm();
  resetRecordForm();
  renderProjects();
  await refreshAll();
}

async function createProject() {
  const button = document.getElementById("createProjectButton");
  const input = document.getElementById("newProjectName");
  const name = input.value.trim();
  if (!name) {
    toast(t("errors.project_name_required"), "error");
    input.focus();
    return;
  }
  setBusy(button, true, "actions.saving");
  try {
    const data = await api("/api/projects/", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    input.value = "";
    await refreshProjects(data.project.id);
    clearTransientResults();
    await refreshAll();
    toast(t("projects.created"), "success");
  } finally {
    setBusy(button, false);
  }
}

async function loadSampleProject() {
  const button = document.getElementById("loadSampleProject");
  setBusy(button, true, "actions.saving");
  try {
    const data = await api("/api/examples/sample-project/", { method: "POST", body: JSON.stringify({}) });
    await refreshProjects(data.project.id);
    clearTransientResults();
    await refreshAll();
    switchTab("dashboard");
    toast(t("projects.sampleCreated"), "success");
  } finally {
    setBusy(button, false);
  }
}

function stepStatus(done, previousDone) {
  if (done) return "complete";
  return previousDone ? "current" : "pending";
}

function renderOnboarding(totals) {
  const fieldsReady = totals.input_count > 0 && totals.output_count > 0;
  const recordsReady = totals.record_count > 0;
  const modelsReady = totals.active_model_count > 0;
  const steps = [
    {
      title: t("onboarding.fieldsTitle"),
      desc: t("onboarding.fieldsDesc"),
      action: t("actions.goFields"),
      tab: "fields",
      done: fieldsReady,
      previousDone: true,
    },
    {
      title: t("onboarding.recordsTitle"),
      desc: t("onboarding.recordsDesc"),
      action: recordsReady ? t("actions.goImport") : t("actions.goRecords"),
      tab: recordsReady ? "import" : "records",
      done: recordsReady,
      previousDone: fieldsReady,
    },
    {
      title: t("onboarding.trainTitle"),
      desc: t("onboarding.trainDesc"),
      action: t("actions.goModels"),
      tab: "models",
      done: modelsReady,
      previousDone: fieldsReady && recordsReady,
    },
    {
      title: t("onboarding.predictTitle"),
      desc: t("onboarding.predictDesc"),
      action: t("actions.goPredict"),
      tab: "predict",
      done: false,
      previousDone: modelsReady,
    },
  ];
  document.getElementById("onboardingSteps").innerHTML = steps
    .map((step, index) => {
      const status = stepStatus(step.done, step.previousDone);
      return `
        <article class="onboarding-step ${status}">
          <div class="step-index">${index + 1}</div>
          <div>
            <strong>${escapeHtml(step.title)}</strong>
            <p>${escapeHtml(step.desc)}</p>
            <span class="step-status">${escapeHtml(t(`onboarding.${status}`))}</span>
          </div>
          <button type="button" class="secondary compact" data-step-tab="${step.tab}">${escapeHtml(step.action)}</button>
        </article>`;
    })
    .join("");
}

async function refreshDashboard() {
  const data = await api("/api/dashboard/summary/");
  state.dashboard = data;
  document.getElementById("projectName").textContent = data.project.name;
  const totals = data.totals;
  const kpis = [
    ["dashboard.kpiFields", totals.field_count],
    ["dashboard.kpiInputs", totals.input_count],
    ["dashboard.kpiOutputs", totals.output_count],
    ["dashboard.kpiRecords", totals.record_count],
    ["dashboard.kpiRuns", totals.model_run_count],
    ["dashboard.kpiActiveModels", totals.active_model_count],
  ];
  document.getElementById("dashboardKpis").innerHTML = kpis
    .map(([labelKey, value]) => `<div class="kpi"><span>${escapeHtml(t(labelKey))}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
  renderOnboarding(totals);
  document.getElementById("onboardingPanel").hidden = Boolean(totals.field_count && totals.record_count && totals.active_model_count);
  document.getElementById("missingnessBody").innerHTML = data.missingness.length
    ? data.missingness
      .map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}<br><small>${escapeHtml(row.field)}</small></td>
          <td>${escapeHtml(t(`roles.${row.role}`))}</td>
          <td>${escapeHtml(row.present_count)}</td>
          <td>${escapeHtml(row.missing_count)}</td>
          <td>${escapeHtml((row.missing_ratio * 100).toFixed(1))}%</td>
        </tr>
      `)
      .join("")
    : emptyRow(t("dashboard.emptyMissingness"), 5);
}

async function refreshFields() {
  const data = await api("/api/fields/");
  state.fields = data.fields;
  document.getElementById("fieldsBody").innerHTML = data.fields.length
    ? data.fields
      .map((field) => `
        <tr>
          <td>${escapeHtml(field.name)}</td>
          <td>${escapeHtml(field.label)}</td>
          <td>${escapeHtml(t(`roles.${field.role}`))}</td>
          <td>${escapeHtml(t(`types.${field.field_type}`))}</td>
          <td>${field.required ? t("boolean.true") : t("boolean.false")}</td>
          <td>${field.is_active ? t("boolean.true") : t("boolean.false")}</td>
          <td class="actions">
            <button class="secondary" data-edit-field="${field.id}">${escapeHtml(t("actions.edit"))}</button>
            <button class="danger" data-delete-field="${field.id}">${escapeHtml(t("actions.delete"))}</button>
          </td>
        </tr>
      `)
      .join("")
    : emptyRow(t("fields.empty"), 7);
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
  const button = document.getElementById("saveFieldButton");
  setBusy(button, true, "actions.saving");
  try {
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
    toast(t("fields.saved"), "success");
  } finally {
    setBusy(button, false);
  }
}

function editField(id) {
  const field = fieldById(id);
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

function confirmAction({ title, message, confirmLabel = t("actions.confirm") }) {
  const modal = document.getElementById("confirmModal");
  const titleEl = document.getElementById("confirmTitle");
  const messageEl = document.getElementById("confirmMessage");
  const ok = document.getElementById("confirmOk");
  const cancel = document.getElementById("confirmCancel");
  const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  titleEl.textContent = title;
  messageEl.textContent = message;
  ok.textContent = confirmLabel;
  modal.hidden = false;
  return new Promise((resolve) => {
    const cleanup = (value) => {
      ok.removeEventListener("click", onOk);
      cancel.removeEventListener("click", onCancel);
      modal.removeEventListener("click", onBackdrop);
      document.removeEventListener("keydown", onKeyDown);
      modal.hidden = true;
      applyI18n();
      previousFocus?.focus();
      resolve(value);
    };
    const onOk = () => cleanup(true);
    const onCancel = () => cleanup(false);
    const onBackdrop = (event) => {
      if (event.target === modal) cleanup(false);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") cleanup(false);
    };
    ok.addEventListener("click", onOk);
    cancel.addEventListener("click", onCancel);
    modal.addEventListener("click", onBackdrop);
    document.addEventListener("keydown", onKeyDown);
    ok.focus();
  });
}

async function deleteField(id) {
  const field = fieldById(id);
  const confirmed = await confirmAction({
    title: t("fields.confirmDeleteTitle"),
    message: t("fields.confirmDelete", { name: field?.label || field?.name || id }),
    confirmLabel: t("actions.delete"),
  });
  if (!confirmed) return;
  await api(`/api/fields/${id}/`, { method: "DELETE" });
  await refreshAll();
  toast(t("fields.deleted"), "success");
}

function inputForField(field, prefix, value = "") {
  const id = `${prefix}-${field.name}`;
  const label = escapeHtml(field.label);
  const fieldName = escapeHtml(field.name);
  if (field.field_type === "boolean") {
    return `
      <label>${label}
        <select id="${id}" data-field="${fieldName}">
          <option value="">${escapeHtml(t("actions.clear"))}</option>
          <option value="true" ${value === true ? "selected" : ""}>${escapeHtml(t("boolean.true"))}</option>
          <option value="false" ${value === false ? "selected" : ""}>${escapeHtml(t("boolean.false"))}</option>
        </select>
      </label>`;
  }
  if (field.field_type === "category" && field.choices && field.choices.length) {
    return `
      <label>${label}
        <select id="${id}" data-field="${fieldName}">
          <option value="">${escapeHtml(t("actions.clear"))}</option>
          ${field.choices.map((choice) => `<option value="${escapeHtml(choice)}" ${choice === value ? "selected" : ""}>${escapeHtml(choice)}</option>`).join("")}
        </select>
      </label>`;
  }
  const type = field.field_type === "number" ? "number" : field.field_type === "datetime" ? "datetime-local" : "text";
  const step = field.field_type === "number" ? ' step="any"' : "";
  const inputValue = valueText(value) === "-" ? "" : valueText(value);
  return `<label>${label}<input id="${id}" data-field="${fieldName}" type="${type}"${step} value="${escapeHtml(inputValue)}"></label>`;
}

function renderDynamicForms() {
  const fields = activeFields();
  const recordFields = fields;
  const predictFields = fields.filter((field) => field.role === "input");
  document.getElementById("recordInputs").innerHTML = recordFields.length
    ? recordFields.map((field) => inputForField(field, "record")).join("")
    : emptyBlock(t("records.emptyFields"));
  document.getElementById("predictInputs").innerHTML = predictFields.length
    ? predictFields.map((field) => inputForField(field, "predict")).join("")
    : emptyBlock(t("predict.emptyInputs"));
  document.getElementById("saveRecordButton").disabled = recordFields.length === 0;
  document.getElementById("predictButton").disabled = predictFields.length === 0;
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
  const button = document.getElementById("saveRecordButton");
  setBusy(button, true, "actions.saving");
  try {
    const id = document.getElementById("recordId").value;
    const values = collectValues("record", activeFields());
    await api(id ? `/api/records/${id}/` : "/api/records/", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(values),
    });
    resetRecordForm();
    await refreshAll();
    toast(t("records.saved"), "success");
  } finally {
    setBusy(button, false);
  }
}

async function refreshRecords() {
  const data = await api("/api/records/");
  state.records = data.records;
  const fields = activeFields();
  if (!fields.length) {
    document.getElementById("recordsHead").innerHTML = "";
    document.getElementById("recordsBody").innerHTML = emptyRow(t("records.emptyFields"), 1);
    return;
  }
  document.getElementById("recordsHead").innerHTML = `
    <tr>
      <th>${escapeHtml(t("tables.id"))}</th>
      ${fields.map((field) => `<th>${escapeHtml(field.label)}<br><small>${escapeHtml(field.name)}</small></th>`).join("")}
      <th>${escapeHtml(t("tables.actions"))}</th>
    </tr>`;
  document.getElementById("recordsBody").innerHTML = data.records.length
    ? data.records
      .map((record) => `
        <tr>
          <td>${escapeHtml(record.id)}</td>
          ${fields.map((field) => `<td>${escapeHtml(valueText(record.values[field.name]))}</td>`).join("")}
          <td class="actions">
            <button class="secondary" data-edit-record="${record.id}">${escapeHtml(t("actions.edit"))}</button>
            <button class="danger" data-delete-record="${record.id}">${escapeHtml(t("actions.delete"))}</button>
          </td>
        </tr>
      `)
      .join("")
    : emptyRow(t("records.emptyRecords"), fields.length + 2);
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
  const confirmed = await confirmAction({
    title: t("records.confirmDeleteTitle"),
    message: t("records.confirmDelete"),
    confirmLabel: t("actions.delete"),
  });
  if (!confirmed) return;
  await api(`/api/records/${id}/`, { method: "DELETE" });
  await refreshAll();
  toast(t("records.deleted"), "success");
}

function importFormData() {
  const file = document.getElementById("importFile").files[0];
  if (!file) throw new ApiError(t("import.chooseFile"), "upload_required");
  const formData = new FormData();
  formData.append("file", file);
  return formData;
}

function renderImportResult(data, mode) {
  state.lastImportResult = data;
  state.lastImportMode = mode;
  const success = data.success !== false;
  const title = mode === "preview"
    ? (success ? t("import.previewPassed") : t("import.previewFailed"))
    : (success ? t("import.commitSuccess") : t("import.commitFailed"));
  const errors = data.errors || [];
  const summary = mode === "preview" || data.valid_count !== undefined
    ? t("import.summary", {
      columns: (data.headers || []).length,
      valid: data.valid_count || 0,
      errors: data.error_count || errors.length || 0,
    })
    : t("import.imported", { count: data.imported_count || 0 });
  const matchedCount = (data.mapped_headers || []).length;
  const unknownColumns = (data.unknown_headers || []).join(", ") || "-";
  const missingColumns = (data.missing_headers || []).join(", ") || "-";
  document.getElementById("importOutput").innerHTML = `
    <div class="result-summary ${success ? "success" : "error"}">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(summary)}</p>
    </div>
    ${mode === "preview" || data.headers ? `
      <div class="import-checks">
        <span>${escapeHtml(t("import.matchedColumns", { count: matchedCount }))}</span>
        <span>${escapeHtml(t("import.unknownColumns", { columns: unknownColumns }))}</span>
        <span>${escapeHtml(t("import.missingColumns", { columns: missingColumns }))}</span>
      </div>
    ` : ""}
    ${errors.length ? `
      <h4>${escapeHtml(t("import.errorsTitle"))}</h4>
      <ul class="error-list">
        ${errors.map((item) => `<li>${item.line ? `${escapeHtml(item.line)}: ` : ""}${escapeHtml(item.error)}</li>`).join("")}
      </ul>
    ` : `<p class="muted">${escapeHtml(t("import.noErrors"))}</p>`}
    <details>
      <summary>${escapeHtml(t("import.raw"))}</summary>
      <pre class="output-box">${escapeHtml(asJson(data))}</pre>
    </details>
  `;
}

async function runImport(path, mode) {
  const button = mode === "preview" ? document.getElementById("previewImport") : document.getElementById("commitImport");
  setBusy(button, true, mode === "preview" ? "actions.previewing" : "actions.importing");
  try {
    const data = await api(path, { method: "POST", body: importFormData(), allowFailure: true });
    renderImportResult(data, mode);
    await refreshAll();
    const toastKey = data.success === false
      ? (mode === "preview" ? "import.previewFailed" : "import.commitFailed")
      : (mode === "preview" ? "import.previewPassed" : "import.commitSuccess");
    toast(t(toastKey), data.success === false ? "error" : "success");
  } finally {
    setBusy(button, false);
  }
}

function formatMetricKey(key) {
  const labels = {
    mae: "MAE",
    rmse: "RMSE",
    r2: "R²",
    accuracy: "Accuracy",
    f1_macro: "Macro F1",
  };
  return labels[key] || key;
}

function formatMetrics(metrics) {
  if (!metrics || !Object.keys(metrics).length) return "-";
  return `<div class="metric-list">${Object.entries(metrics)
    .map(([key, value]) => `<span><b>${escapeHtml(formatMetricKey(key))}</b>${escapeHtml(value ?? "-")}</span>`)
    .join("")}</div>`;
}

function trainingNoticeForTarget(targetName) {
  const target = state.lastTrainingResult?.targets?.[targetName];
  if (!target || target.success !== false) return "";
  const message = localizeErrorPayload(target);
  return `
    <div class="result-summary error compact-summary">
      <strong>${escapeHtml(t("models.targetFailed"))}</strong>
      <p>${escapeHtml(message)}</p>
      <p><b>${escapeHtml(t("models.nextStep"))}:</b> ${escapeHtml(t("models.needMoreRows"))}</p>
    </div>`;
}

async function refreshModels() {
  const data = await api("/api/models/summary/");
  document.getElementById("modelsList").innerHTML = data.targets.length
    ? data.targets
      .map((target) => `
        <div class="model-card">
          <h4>${escapeHtml(target.target.label)} <small>${escapeHtml(target.target.name)}</small></h4>
          <p>${escapeHtml(t("models.taskType"))}: ${escapeHtml(t(`taskTypes.${target.task_type}`))}</p>
          ${trainingNoticeForTarget(target.target.name)}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${escapeHtml(t("models.model"))}</th>
                  <th>${escapeHtml(t("models.metrics"))}</th>
                  <th>${escapeHtml(t("models.samples"))}</th>
                  <th>${escapeHtml(t("models.status"))}</th>
                  <th>${escapeHtml(t("tables.actions"))}</th>
                </tr>
              </thead>
              <tbody>
                ${target.runs.length ? target.runs.map((run) => `
                  <tr>
                    <td>${escapeHtml(run.candidate_label)}</td>
                    <td>${run.error_message ? `<span class="error-text">${escapeHtml(run.error_message)}</span>` : formatMetrics(run.metrics)}</td>
                    <td>${escapeHtml(run.training_sample_count)}</td>
                    <td>
                      ${run.error_message ? `<span class="pill failed">${escapeHtml(t("models.failed"))}</span>` : ""}
                      ${run.is_active ? `<span class="pill active">${escapeHtml(t("models.active"))}</span>` : ""}
                      ${run.is_recommended ? `<span class="pill recommended">${escapeHtml(t("models.recommended"))}</span>` : ""}
                    </td>
                    <td>${run.error_message ? "-" : `<button class="secondary" data-activate-model="${run.id}">${escapeHtml(t("actions.activate"))}</button>`}</td>
                  </tr>
                `).join("") : emptyRow(t("models.noRuns"), 5)}
              </tbody>
            </table>
          </div>
        </div>
      `)
      .join("")
    : emptyBlock(t("models.empty"));
}

async function trainModels() {
  const button = document.getElementById("trainModels");
  setBusy(button, true, "actions.training");
  document.getElementById("modelsList").innerHTML = `<div class="model-card loading-card">${escapeHtml(t("actions.training"))}</div>`;
  try {
    const data = await api("/api/train/", { method: "POST", body: JSON.stringify({}), allowFailure: true });
    state.lastTrainingResult = data;
    await refreshModels();
    await refreshDashboard();
    if (data.training_status === "failed") {
      toast(t("models.trainingFailed"), "error");
    } else if (data.training_status === "partial") {
      toast(t("models.trainingPartial"), "info");
    } else {
      toast(t("models.trained"), "success");
    }
  } finally {
    setBusy(button, false);
  }
}

async function activateModel(id) {
  await api("/api/models/activate/", { method: "POST", body: JSON.stringify({ model_run_id: Number(id) }) });
  await refreshModels();
  await refreshDashboard();
  toast(t("models.activated"), "success");
}

function renderPredictionResults(results) {
  state.lastPredictionResults = results || {};
  state.lastPredictionAction = "";
  const entries = Object.entries(results || {});
  if (!entries.length) {
    document.getElementById("predictOutput").innerHTML = emptyBlock(t("predict.emptyResults"));
    return;
  }
  document.getElementById("predictOutput").innerHTML = entries
    .map(([name, result]) => `
      <div class="prediction-card">
        <h4>${escapeHtml(result.target_label || name)} <small>${escapeHtml(name)}</small></h4>
        <div class="prediction-value">
          <span>${escapeHtml(t("predict.prediction"))}</span>
          <strong>${escapeHtml(valueText(result.prediction))}</strong>
        </div>
        <p>${escapeHtml(t("predict.model"))}: ${escapeHtml(result.model?.candidate_label || "-")}</p>
        <details>
          <summary>${escapeHtml(t("predict.raw"))}</summary>
          <pre class="output-box">${escapeHtml(asJson(result))}</pre>
        </details>
      </div>
    `)
    .join("");
}

function renderPredictionAction(message) {
  state.lastPredictionAction = "no_active_model";
  document.getElementById("predictOutput").innerHTML = `
    <div class="result-summary info">
      <strong>${escapeHtml(t("predict.resultTitle"))}</strong>
      <p>${escapeHtml(message)}</p>
      <button type="button" class="secondary compact" data-step-tab="models">${escapeHtml(t("actions.goModels"))}</button>
    </div>`;
}

async function runPredict(event) {
  event.preventDefault();
  const button = document.getElementById("predictButton");
  setBusy(button, true, "actions.predicting");
  try {
    const fields = activeFields().filter((field) => field.role === "input");
    const payload = collectValues("predict", fields);
    const data = await api("/api/predict/", { method: "POST", body: JSON.stringify(payload) });
    renderPredictionResults(data.results);
  } catch (error) {
    if (error instanceof ApiError && error.code === "no_active_model") {
      renderPredictionAction(t("predict.noActiveAction"));
    }
    throw error;
  } finally {
    setBusy(button, false);
  }
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
  if (target.dataset.stepTab) switchTab(target.dataset.stepTab);
  if (target.dataset.editField) editField(target.dataset.editField);
  if (target.dataset.deleteField) {
    try { await deleteField(target.dataset.deleteField); } catch (error) { toast(localizeError(error), "error"); }
  }
  if (target.dataset.editRecord) editRecord(target.dataset.editRecord);
  if (target.dataset.deleteRecord) {
    try { await deleteRecord(target.dataset.deleteRecord); } catch (error) { toast(localizeError(error), "error"); }
  }
  if (target.dataset.activateModel) {
    try { await activateModel(target.dataset.activateModel); } catch (error) { toast(localizeError(error), "error"); }
  }
});

document.getElementById("languageSelect").addEventListener("change", (event) => setLanguage(event.target.value));
document.getElementById("projectSelect").addEventListener("change", (event) => {
  changeProject(event.target.value).catch((error) => toast(localizeError(error), "error"));
});
document.getElementById("createProjectButton").addEventListener("click", () => createProject().catch((error) => toast(localizeError(error), "error")));
document.getElementById("newProjectName").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    createProject().catch((error) => toast(localizeError(error), "error"));
  }
});
document.getElementById("loadSampleProject").addEventListener("click", () => loadSampleProject().catch((error) => toast(localizeError(error), "error")));
document.getElementById("fieldForm").addEventListener("submit", (event) => saveField(event).catch((error) => toast(localizeError(error), "error")));
document.getElementById("recordForm").addEventListener("submit", (event) => saveRecord(event).catch((error) => toast(localizeError(error), "error")));
document.getElementById("predictForm").addEventListener("submit", (event) => runPredict(event).catch((error) => toast(localizeError(error), "error")));
document.getElementById("resetFieldForm").addEventListener("click", resetFieldForm);
document.getElementById("resetRecordForm").addEventListener("click", resetRecordForm);
document.getElementById("refreshDashboard").addEventListener("click", () => refreshDashboard().catch((error) => toast(localizeError(error), "error")));
document.getElementById("refreshModels").addEventListener("click", () => refreshModels().catch((error) => toast(localizeError(error), "error")));
document.getElementById("trainModels").addEventListener("click", () => trainModels().catch((error) => toast(localizeError(error), "error")));
document.getElementById("previewImport").addEventListener("click", () => runImport("/api/import/preview/", "preview").catch((error) => toast(localizeError(error), "error")));
document.getElementById("commitImport").addEventListener("click", () => runImport("/api/import/commit/", "commit").catch((error) => toast(localizeError(error), "error")));

applyI18n();
renderPredictionResults({});
refreshProjects()
  .then(refreshAll)
  .then(resetFieldForm)
  .catch((error) => toast(localizeError(error), "error"));

const titles = {
  lh: ["LH 공고 일정 확인", "지역별 접수예정/접수중 공고를 확인한 뒤 선택 분석합니다."],
  hug: ["HUG 직접 파싱", "파싱 전 지역을 선택하거나 직접 입력합니다."],
  sh: ["SH 공고 일정 확인", "검색어 조합으로 SH 공고를 확인한 뒤 선택 분석합니다."],
  gh: ["GH 상태별 자료 수집", "공고 일정, 접수중 실시간 경쟁률, 최근 마감 최종 경쟁률을 공고별로 저장합니다."],
  results: ["결과 확인", "기관별 최종 산출물을 확인합니다."],
  settings: ["설정", "표준 위치와 요약 기준을 확인합니다."],
};

const title = document.querySelector("#view-title");
const subtitle = document.querySelector("#view-subtitle");
const logText = document.querySelector("#log-text");
const statusPill = document.querySelector(".status-pill");
const lhNoticeList = document.querySelector("#lh-notice-list");
const lhRunSelectedNotices = document.querySelector("#lh-run-selected-notices");
const shNoticeList = document.querySelector("#sh-notice-list");
const shRunSelectedNotices = document.querySelector("#sh-run-selected-notices");
let lhNoticeCandidates = [];
let shNoticeCandidates = [];

const regionControls = {
  lh: {
    label: "LH",
    selectedKey: "lhSelectedRegionsV1",
    customKey: "lhCustomRegionsV1",
    selected: new Set(JSON.parse(localStorage.getItem("lhSelectedRegionsV1") || "[]")),
    custom: new Set(JSON.parse(localStorage.getItem("lhCustomRegionsV1") || "[]")),
    grid: document.querySelector("#lh-region-grid"),
    input: document.querySelector("#lh-manual-region-input"),
    addButton: document.querySelector("#lh-add-region"),
    resetButton: document.querySelector("#lh-reset-regions"),
    runButton: document.querySelector("#lh-run-collect"),
    endpoint: "/api/lh/notices",
  },
  hug: {
    label: "HUG",
    selectedKey: "hugSelectedRegionsV2",
    customKey: "hugCustomRegionsV2",
    selected: new Set(JSON.parse(localStorage.getItem("hugSelectedRegionsV2") || "[]")),
    custom: new Set(JSON.parse(localStorage.getItem("hugCustomRegionsV2") || "[]")),
    grid: document.querySelector("#hug-region-grid"),
    input: document.querySelector("#hug-manual-region-input"),
    addButton: document.querySelector("#hug-add-region"),
    resetButton: document.querySelector("#hug-reset-regions"),
    runButton: document.querySelector("#hug-run-collect"),
    endpoint: "/api/hug/collect",
  },
  sh: {
    label: "SH",
    selectedKey: "shSelectedKeywordsV1",
    customKey: "shCustomKeywordsV1",
    selected: new Set(JSON.parse(localStorage.getItem("shSelectedKeywordsV1") || "[]")),
    custom: new Set(JSON.parse(localStorage.getItem("shCustomKeywordsV1") || "[]")),
    grid: document.querySelector("#sh-region-grid"),
    input: document.querySelector("#sh-manual-region-input"),
    addButton: document.querySelector("#sh-add-region"),
    resetButton: document.querySelector("#sh-reset-regions"),
    runButton: document.querySelector("#sh-run-collect"),
    endpoint: "/api/sh/notices",
  },
  gh: {
    label: "GH",
    selectedKey: "ghSelectedKeywordsV1",
    customKey: "ghCustomKeywordsV1",
    selected: new Set(JSON.parse(localStorage.getItem("ghSelectedKeywordsV1") || "[]")),
    custom: new Set(JSON.parse(localStorage.getItem("ghCustomKeywordsV1") || "[]")),
    grid: document.querySelector("#gh-region-grid"),
    input: document.querySelector("#gh-manual-region-input"),
    addButton: document.querySelector("#gh-add-region"),
    resetButton: document.querySelector("#gh-reset-regions"),
    runButton: document.querySelector("#gh-run-collect"),
    endpoint: "/api/gh/collect",
  },
};

function setLog(message) {
  logText.textContent = message;
}

const progressPanel = document.querySelector(".progress-panel");
const progressTitle = document.querySelector("#progress-title");
const progressPercent = document.querySelector("#progress-percent");
const progressFill = document.querySelector("#progress-fill");
const progressTrack = document.querySelector(".progress-track");
const progressDetail = document.querySelector("#progress-detail");
let progressTimer = null;
let progressValue = 0;

const progressProfiles = {
  "/api/lh/notices": {
    title: "LH 공고 일정 확인 중",
    stages: [
      [8, "선택 지역을 확인하고 LH 공고 목록을 불러오고 있습니다."],
      [34, "공고별 접수기간을 확인하는 중입니다."],
      [68, "접수마감 공고를 제외하고 후보 목록을 정리하고 있습니다."],
      [86, "분석 가능한 공고를 화면에 표시하는 중입니다."],
    ],
  },
  "/api/lh/collect": {
    title: "LH 선택 공고 분석 중",
    stages: [
      [8, "선택한 LH 공고를 확인하고 있습니다."],
      [28, "공고 상세 페이지의 접수/공급 정보를 읽고 있습니다."],
      [58, "LH 상세 페이지의 공급/신청 표를 수집하는 중입니다."],
      [82, "경쟁률 CSV와 TXT 보고서를 저장하는 중입니다."],
    ],
  },
  "/api/hug/collect": {
    title: "HUG 파싱 진행 중",
    stages: [
      [8, "선택 지역을 확인하고 HUG 페이지에 접속하고 있습니다."],
      [28, "지역별 공고 목록을 수집하는 중입니다."],
      [58, "보증금, 신청자수, 거리 정보를 계산하는 중입니다."],
      [82, "분석 CSV와 요약 TXT를 저장하는 중입니다."],
    ],
  },
  "/api/sh/notices": {
    title: "SH 공고 일정 확인 중",
    stages: [
      [8, "선택 검색어를 확인하고 SH 공고 목록을 검색하고 있습니다."],
      [30, "공고 상세 페이지를 열어 접수일정을 확인하는 중입니다."],
      [62, "접수마감 또는 일정 미확인 공고를 제외하고 있습니다."],
      [86, "선택 가능한 SH 공고를 화면에 표시하는 중입니다."],
    ],
  },
  "/api/sh/collect": {
    title: "SH 선택 공고 분석 중",
    stages: [
      [8, "선택한 SH 공고를 확인하고 있습니다."],
      [32, "상세 본문과 첨부파일 메타정보를 수집하는 중입니다."],
      [58, "접수일정과 표준 지표를 매핑하는 중입니다."],
      [82, "SH 분석 CSV와 요약 TXT를 저장하는 중입니다."],
    ],
  },
  "/api/gh/collect": {
    title: "GH 상태별 자료 수집 중",
    stages: [
      [8, "GH 공고중 목록과 상세 일정을 확인하고 있습니다."],
      [30, "접수중 공고의 실시간 경쟁률 표를 수집하고 있습니다."],
      [58, "최근 접수마감 공고의 최종 경쟁률을 확인하는 중입니다."],
      [82, "전체 및 일반공급 경쟁률 CSV와 TXT 요약을 저장하는 중입니다."],
    ],
  },
};

function progressProfile(path) {
  return progressProfiles[path] || {
    title: "작업 진행 중",
    stages: [[20, "요청을 처리하고 있습니다."], [70, "결과를 정리하고 있습니다."]],
  };
}

function setProgress(value, detail = "") {
  progressValue = Math.max(0, Math.min(100, Math.round(value)));
  progressFill.style.width = `${progressValue}%`;
  progressPercent.textContent = `${progressValue}%`;
  progressTrack.setAttribute("aria-valuenow", String(progressValue));
  if (detail) progressDetail.textContent = detail;
}

function stageFor(profile, value) {
  let detail = profile.stages[0]?.[1] || "작업을 준비하고 있습니다.";
  profile.stages.forEach(([threshold, message]) => {
    if (value >= threshold) detail = message;
  });
  return detail;
}

function startProgress(path) {
  const profile = progressProfile(path);
  clearInterval(progressTimer);
  progressPanel.classList.add("is-active");
  progressPanel.classList.remove("is-complete", "is-error");
  progressTitle.textContent = profile.title;
  setProgress(3, profile.stages[0]?.[1] || "작업을 시작하고 있습니다.");

  progressTimer = setInterval(() => {
    const distance = 92 - progressValue;
    if (distance <= 0) return;
    const step = Math.max(1, Math.ceil(distance * 0.08));
    const next = Math.min(92, progressValue + step);
    setProgress(next, stageFor(profile, next));
  }, 700);
}

function finishProgress(message = "작업이 완료되었습니다.") {
  clearInterval(progressTimer);
  progressTimer = null;
  progressPanel.classList.add("is-complete");
  setProgress(100, message);
  window.setTimeout(() => {
    progressPanel.classList.remove("is-active", "is-complete");
  }, 1600);
}

function failProgress(message = "작업에 실패했습니다.") {
  clearInterval(progressTimer);
  progressTimer = null;
  progressPanel.classList.add("is-active", "is-error");
  progressPanel.classList.remove("is-complete");
  setProgress(progressValue || 100, message);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.message || "요청 처리에 실패했습니다.");
  }
  return data;
}

function button(label, path, action) {
  return `<button data-result-action="${action}" data-path="${path}">${label}</button>`;
}

function renderResults(results) {
  const table = document.querySelector(".result-table");
  const rows = results.map((item) => `
    <div class="row">
      <span>${item.source}</span>
      <span>${item.name}</span>
      <strong>${item.status}</strong>
      <div class="actions">
        ${button("열기", item.relativePath, "open")}
        ${button("폴더", item.relativePath, "folder")}
        ${button("내보내기", item.relativePath, "download")}
      </div>
    </div>
  `);
  table.innerHTML = `
    <div class="row head"><span>기관</span><span>파일</span><span>상태</span><span>작업</span></div>
    ${rows.join("")}
  `;
}

function renderMetricState(metrics) {
  const path = document.querySelector("#metrics-path");
  const count = document.querySelector("#metrics-count");
  if (!metrics) return;
  if (path) path.textContent = "app/config/metrics_registry.json";
  if (count) count.textContent = `${metrics.metricCount || 0}개 등록`;
}

function renderLhNotices(notices) {
  lhNoticeCandidates = notices || [];
  lhNoticeList.innerHTML = "";
  if (!lhNoticeCandidates.length) {
    const empty = document.createElement("div");
    empty.className = "notice-empty";
    empty.textContent = "접수예정 또는 접수중 LH 공고가 없습니다.";
    lhNoticeList.appendChild(empty);
    lhRunSelectedNotices.disabled = true;
    return;
  }

  const header = document.createElement("div");
  header.className = "notice-row notice-head";
  header.innerHTML = "<span>선택</span><span>상태</span><span>지역</span><span>공고명</span><span>접수기간</span>";
  lhNoticeList.appendChild(header);

  lhNoticeCandidates.forEach((notice) => {
    const row = document.createElement("label");
    row.className = "notice-row";

    const checkWrap = document.createElement("span");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = notice.id;
    checkbox.checked = true;
    checkbox.addEventListener("change", updateLhNoticeAnalyzeState);
    checkWrap.appendChild(checkbox);

    const status = document.createElement("strong");
    status.textContent = notice.status;
    status.className = notice.status === "접수중" ? "notice-status live" : "notice-status";

    const region = document.createElement("span");
    region.textContent = notice.notice_region || notice.requested_region;

    const titleText = document.createElement("span");
    titleText.textContent = notice.title;

    const period = document.createElement("span");
    period.textContent = `${notice.apply_start || "확인필요"} ~ ${notice.apply_end || "확인필요"}`;

    row.append(checkWrap, status, region, titleText, period);
    lhNoticeList.appendChild(row);
  });
  updateLhNoticeAnalyzeState();
}

function selectedLhNotices() {
  const selectedIds = new Set(
    Array.from(lhNoticeList.querySelectorAll('input[type="checkbox"]:checked')).map((item) => item.value)
  );
  return lhNoticeCandidates.filter((notice) => selectedIds.has(notice.id));
}

function updateLhNoticeAnalyzeState() {
  lhRunSelectedNotices.disabled = selectedLhNotices().length === 0;
}

function renderShNotices(notices) {
  shNoticeCandidates = notices || [];
  shNoticeList.innerHTML = "";
  if (!shNoticeCandidates.length) {
    const empty = document.createElement("div");
    empty.className = "notice-empty";
    empty.textContent = "접수예정 또는 접수중 SH 공고가 없습니다.";
    shNoticeList.appendChild(empty);
    shRunSelectedNotices.disabled = true;
    return;
  }

  const header = document.createElement("div");
  header.className = "notice-row notice-head";
  header.innerHTML = "<span>선택</span><span>상태</span><span>검색어</span><span>공고명</span><span>접수기간</span>";
  shNoticeList.appendChild(header);

  shNoticeCandidates.forEach((notice) => {
    const row = document.createElement("label");
    row.className = "notice-row";

    const checkWrap = document.createElement("span");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = notice.id;
    checkbox.checked = true;
    checkbox.addEventListener("change", updateShNoticeAnalyzeState);
    checkWrap.appendChild(checkbox);

    const status = document.createElement("strong");
    status.textContent = notice.status;
    status.className = notice.status === "접수중" ? "notice-status live" : "notice-status";

    const region = document.createElement("span");
    region.textContent = notice.notice_region || notice.requested_region;

    const titleText = document.createElement("span");
    titleText.textContent = notice.title;

    const period = document.createElement("span");
    period.textContent = `${notice.apply_start || "확인필요"} ~ ${notice.apply_end || "확인필요"}`;

    row.append(checkWrap, status, region, titleText, period);
    shNoticeList.appendChild(row);
  });
  updateShNoticeAnalyzeState();
}

function selectedShNotices() {
  const selectedIds = new Set(
    Array.from(shNoticeList.querySelectorAll('input[type="checkbox"]:checked')).map((item) => item.value)
  );
  return shNoticeCandidates.filter((notice) => selectedIds.has(notice.id));
}

function updateShNoticeAnalyzeState() {
  shRunSelectedNotices.disabled = selectedShNotices().length === 0;
}

function saveRegionState(type) {
  const state = regionControls[type];
  localStorage.setItem(state.selectedKey, JSON.stringify(Array.from(state.selected)));
  localStorage.setItem(state.customKey, JSON.stringify(Array.from(state.custom)));
}

function createRegionOption(type, name) {
  const state = regionControls[type];
  const item = document.createElement("div");
  item.className = "region-option is-custom";

  const label = document.createElement("label");
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.value = name;
  checkbox.checked = state.selected.has(name);
  checkbox.addEventListener("change", (event) => {
    if (event.target.checked) state.selected.add(name);
    else state.selected.delete(name);
    saveRegionState(type);
  });

  const text = document.createElement("span");
  text.textContent = name;
  label.append(checkbox, text);

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "region-remove";
  removeButton.textContent = "삭제";
    removeButton.title = `${name} 삭제`;
  removeButton.addEventListener("click", () => {
    state.custom.delete(name);
    state.selected.delete(name);
    saveRegionState(type);
    renderRegions(type);
    setLog(`${state.label} ${name} 항목을 선택 목록에서 삭제했습니다.`);
  });

  item.append(label, removeButton);
  return item;
}

function renderRegions(type) {
  const state = regionControls[type];
  Array.from(state.selected).forEach((name) => {
    if (!state.custom.has(name)) state.selected.delete(name);
  });
  const visibleRegions = Array.from(state.custom).sort((left, right) => left.localeCompare(right, "ko"));
  state.grid.innerHTML = "";
  if (!visibleRegions.length) {
    const empty = document.createElement("div");
    empty.className = "region-empty";
    empty.textContent = type === "sh" || type === "gh" ? "추가된 검색어 없음" : "추가된 지역 없음";
    state.grid.appendChild(empty);
  } else {
    visibleRegions.forEach((name) => state.grid.appendChild(createRegionOption(type, name)));
  }
  saveRegionState(type);
}

function addRegion(type) {
  const state = regionControls[type];
  const value = state.input.value.trim();
  if (!value) {
    setLog(type === "sh" || type === "gh" ? "추가할 검색어를 입력하세요." : "추가할 지역명을 입력하세요.");
    return;
  }
  state.custom.add(value);
  state.selected.add(value);
  saveRegionState(type);
  renderRegions(type);
  state.input.value = "";
  setLog(`${state.label} ${value} 항목을 선택 목록에 추가했습니다.`);
}

function resetRegions(type) {
  const state = regionControls[type];
  state.custom.clear();
  state.selected.clear();
  saveRegionState(type);
  renderRegions(type);
  if (type === "lh") renderLhNotices([]);
  if (type === "sh") renderShNotices([]);
  setLog(type === "sh" || type === "gh" ? `${state.label} 검색어 선택을 초기화했습니다.` : `${state.label} 지역 선택을 초기화했습니다.`);
}

async function refreshState() {
  try {
    const state = await api("/api/state");
    statusPill.lastChild.textContent = state.layoutOk ? " 표준 구조 확인됨" : " 표준 구조 확인 필요";
    renderMetricState(state.metrics);
    renderRegions("lh");
    renderRegions("hug");
    renderRegions("sh");
    renderRegions("gh");
    renderResults(state.results);
    setLog("현재 상태를 새로고침했습니다.");
  } catch (error) {
    setLog(`상태 확인 실패: ${error.message}`);
  }
}

async function postAction(path, body = {}, trigger = null) {
  const originalHtml = trigger ? trigger.innerHTML : "";
  if (trigger) {
    trigger.disabled = true;
    trigger.classList.add("is-busy");
    trigger.innerHTML = "실행 중...";
  }
  startProgress(path);
  try {
    setLog("작업을 실행 중입니다. 진행 상태는 상단 게이지에서 확인할 수 있습니다.");
    const data = await api(path, { method: "POST", body: JSON.stringify(body) });
    if (data.results) renderResults(data.results);
    const message = data.message || "작업이 완료되었습니다.";
    setLog(message);
    finishProgress(message);
    return data;
  } catch (error) {
    failProgress(error.message);
    throw error;
  } finally {
    if (trigger) {
      trigger.disabled = false;
      trigger.classList.remove("is-busy");
      trigger.innerHTML = originalHtml;
    }
  }
}

function selectedRegionList(type) {
  return Array.from(regionControls[type].selected);
}

document.querySelectorAll(".tab").forEach((buttonElement) => {
  buttonElement.addEventListener("click", () => {
    const target = buttonElement.dataset.tab;
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("is-active"));
    document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("is-active"));
    buttonElement.classList.add("is-active");
    document.querySelector(`#panel-${target}`).classList.add("is-active");
    title.textContent = titles[target][0];
    subtitle.textContent = titles[target][1];
    if (target === "results") refreshState();
    else setLog(`${titles[target][0]} 탭으로 이동했습니다.`);
  });
});

Object.entries(regionControls).forEach(([type, state]) => {
  state.addButton.addEventListener("click", () => addRegion(type));
  state.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addRegion(type);
    }
  });
  state.resetButton.addEventListener("click", () => resetRegions(type));
  state.runButton.addEventListener("click", async (event) => {
    try {
      const data = await postAction(state.endpoint, { regions: selectedRegionList(type) }, event.currentTarget);
      if (type === "lh") {
        renderLhNotices(data.notices || []);
      } else if (type === "sh") {
        renderShNotices(data.notices || []);
      } else {
        await refreshState();
      }
    } catch (error) {
      setLog(`${state.label} 파싱 실패: ${error.message}`);
    }
  });
});

lhRunSelectedNotices.addEventListener("click", async (event) => {
  try {
    const notices = selectedLhNotices();
    if (!notices.length) {
      setLog("분석할 LH 공고를 하나 이상 선택하세요.");
      return;
    }
    await postAction("/api/lh/collect", { notices }, event.currentTarget);
    await refreshState();
  } catch (error) {
    setLog(`LH 선택 공고 분석 실패: ${error.message}`);
  }
});

shRunSelectedNotices.addEventListener("click", async (event) => {
  try {
    const notices = selectedShNotices();
    if (!notices.length) {
      setLog("분석할 SH 공고를 하나 이상 선택하세요.");
      return;
    }
    await postAction("/api/sh/collect", { notices }, event.currentTarget);
    await refreshState();
  } catch (error) {
    setLog(`SH 선택 공고 분석 실패: ${error.message}`);
  }
});

document.querySelector("#panel-results .icon-button").addEventListener("click", refreshState);

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-result-action]");
  if (!target) return;
  const path = target.dataset.path;
  const action = target.dataset.resultAction;
  try {
    if (action === "download") {
      window.location.href = `/api/download?path=${encodeURIComponent(path)}`;
      setLog(`${path} 내보내기를 시작했습니다.`);
      return;
    }
    await postAction(`/api/file/${action}`, { path });
  } catch (error) {
    setLog(`파일 작업 실패: ${error.message}`);
  }
});

refreshState();

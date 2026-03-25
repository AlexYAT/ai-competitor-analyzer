(function () {
  const $ = (id) => document.getElementById(id);

  const niche = $("niche");
  const siteType = $("site_type");
  const region = $("region");
  const maxResults = $("max_results");
  const btnFind = $("btn-find");
  const btnAnalyze = $("btn-analyze");
  const statusFind = $("status-find");
  const statusAnalyze = $("status-analyze");
  const errorFind = $("error-find");
  const errorAnalyze = $("error-analyze");
  const resultsSection = $("results-section");
  const resultsList = $("results-list");
  const reportSection = $("report-section");
  const reportOut = $("report-out");
  const reportLang = $("report_lang");

  let lastResults = [];
  let isBusy = false;

  function clearErrors() {
    errorFind.textContent = "";
    errorAnalyze.textContent = "";
  }

  function updateUiState() {
    const hasResults = lastResults.length > 0;
    btnFind.disabled = isBusy;
    btnAnalyze.disabled = isBusy || !hasResults;
  }

  function setBusy(busy) {
    isBusy = busy;
    updateUiState();
  }

  function parseErrorDetail(data) {
    if (data && typeof data.detail === "string") return data.detail;
    if (data && Array.isArray(data.detail)) {
      return data.detail.map((x) => x.msg || JSON.stringify(x)).join("; ");
    }
    return null;
  }

  async function postJson(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { raw: text };
    }
    if (!res.ok) {
      const msg = parseErrorDetail(data) || data?.raw || res.statusText;
      throw new Error(msg || `HTTP ${res.status}`);
    }
    return data;
  }

  /** Allowed browser navigation targets: only http/https. Otherwise null (render as plain text). */
  function safeHttpUrl(u) {
    try {
      const url = new URL(String(u).trim());
      if (url.protocol !== "http:" && url.protocol !== "https:") return null;
      return url.href;
    } catch {
      return null;
    }
  }

  /** Paragraph: clickable link only when URL is safe http(s); else escaped text only. */
  function urlLineHtml(raw) {
    const display = String(raw ?? "");
    const href = safeHttpUrl(raw);
    if (href) {
      return `<p class="result-url"><a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(display)}</a></p>`;
    }
    return `<p class="result-url">${escapeHtml(display || "—")}</p>`;
  }

  function renderResults(candidates) {
    resultsList.innerHTML = "";
    candidates.forEach((c, i) => {
      const id = `cb-${i}`;
      const row = document.createElement("div");
      row.className = "result-item";
      row.innerHTML = `
        <input type="checkbox" id="${id}" value="${i}" />
        <div class="result-body">
          <p class="result-title">${escapeHtml(c.title || "(без названия)")}</p>
          ${urlLineHtml(c.url)}
          <p class="result-snippet">${escapeHtml(c.description || "—")}</p>
        </div>
      `;
      resultsList.appendChild(row);
    });
    resultsSection.hidden = candidates.length === 0;
    updateUiState();
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getSelectedUrls() {
    const boxes = resultsList.querySelectorAll('input[type="checkbox"]:checked');
    const urls = [];
    boxes.forEach((b) => {
      const idx = parseInt(b.value, 10);
      if (lastResults[idx]) urls.push(lastResults[idx].url);
    });
    return urls;
  }

  const REPORT_FAIL_LABELS = {
    timeout: "Не удалось загрузить страницу (таймаут)",
    selenium_error: "Ошибка браузера при загрузке",
    invalid_url: "Некорректный URL",
    llm_error: "Ошибка анализа (LLM)",
  };

  function reportFailLabel(reason, message) {
    const base = REPORT_FAIL_LABELS[reason];
    if (base && message) return `${base}: ${message}`;
    if (base) return base;
    return message || reason || "Ошибка";
  }

  function renderReport(data) {
    const { items = [], summary } = data;
    let html = "";

    if (summary) {
      html += `<h3>Сводка по рынку</h3>`;
      html += `<p>${escapeHtml(summary.market_summary || "")}</p>`;
      html += `<h3>Общие сильные стороны</h3><ul>`;
      (summary.common_strengths || []).forEach((x) => {
        html += `<li>${escapeHtml(x)}</li>`;
      });
      html += `</ul><h3>Общие слабости</h3><ul>`;
      (summary.common_weaknesses || []).forEach((x) => {
        html += `<li>${escapeHtml(x)}</li>`;
      });
      html += `</ul><h3>Возможности дифференциации</h3><ul>`;
      (summary.differentiation_opportunities || []).forEach((x) => {
        html += `<li>${escapeHtml(x)}</li>`;
      });
      html += `</ul>`;
    }

    html += `<h3>Карточки конкурентов</h3>`;
    items.forEach((it) => {
      if (it.status === "failed") {
        const msg = reportFailLabel(it.reason, it.message || "");
        html += `<div class="item-card item-failed">
          <p class="result-url"><strong>Не обработано</strong></p>
          ${urlLineHtml(it.url)}
          <p>${escapeHtml(msg)}</p>
        </div>`;
        return;
      }
      const a = it.analysis || {};
      const linkUrl = a.final_url || a.url || it.url;
      html += `<div class="item-card">
        <strong>${escapeHtml(a.title || "")}</strong>
        ${urlLineHtml(linkUrl)}
        <p><strong>Позиционирование:</strong> ${escapeHtml(a.positioning || "")}</p>
        <p><strong>Оффер:</strong> ${escapeHtml(a.offer || "")}</p>
        <p><strong>Аудитория:</strong> ${escapeHtml(a.target_audience || "")}</p>
        <p class="scores">design_score: ${escapeHtml(String(a.design_score))} · animation_potential: ${escapeHtml(String(a.animation_potential))}</p>
        <p><strong>Сильные стороны:</strong></p><ul>${(a.strengths || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
        <p><strong>Слабости:</strong></p><ul>${(a.weaknesses || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
        <p>${escapeHtml(a.summary || "")}</p>
      </div>`;
    });

    reportOut.innerHTML = html;
    reportSection.hidden = false;
  }

  btnFind.addEventListener("click", async () => {
    clearErrors();
    const q = (niche.value || "").trim();
    if (!q) {
      errorFind.textContent = "Введите нишу или запрос.";
      return;
    }

    setBusy(true);
    statusFind.textContent = "Поиск…";
    reportSection.hidden = true;
    reportOut.innerHTML = "";

    try {
      const body = {
        niche: q,
        site_type: siteType.value,
        max_results: Math.min(50, Math.max(1, parseInt(maxResults.value, 10) || 10)),
      };
      const reg = (region.value || "").trim();
      if (reg) body.region = reg;

      const data = await postJson("/find-competitors", body);
      lastResults = data.filtered_results || [];
      renderResults(lastResults);
      statusFind.textContent =
        lastResults.length > 0
          ? `Готово. Запрос: «${data.query_used || q}». Строк в выдаче: ${data.raw_results_count}, после фильтра: ${lastResults.length}.`
          : "Готово, но список пуст.";
    } catch (e) {
      statusFind.textContent = "";
      errorFind.textContent = e.message || String(e);
      lastResults = [];
      resultsSection.hidden = true;
      updateUiState();
    } finally {
      setBusy(false);
    }
  });

  btnAnalyze.addEventListener("click", async () => {
    clearErrors();
    const urls = getSelectedUrls();
    if (urls.length === 0) {
      errorAnalyze.textContent = "Выберите хотя бы один сайт.";
      return;
    }

    setBusy(true);
    statusAnalyze.textContent = "Анализ и отчёт (Selenium + LLM)…";

    try {
      const lang = (reportLang && reportLang.value) || "ru";
      const data = await postJson("/reportdemo", { urls, lang });
      renderReport(data);
      statusAnalyze.textContent = "Готово.";
    } catch (e) {
      statusAnalyze.textContent = "";
      errorAnalyze.textContent = e.message || String(e);
    } finally {
      setBusy(false);
    }
  });

  updateUiState();
})();

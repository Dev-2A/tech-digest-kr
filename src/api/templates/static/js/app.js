const API = "";
let currentFilter = "all";

// === 초기화 ===
document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadArticles();
  loadTags();
});

// === 통계 ===
async function loadStats() {
  try {
    const res = await fetch(`${API}/api/settings/stats`);
    const data = await res.json();
    document.getElementById("stat-total").textContent = data.total_articles;
    document.getElementById("stat-unread").textContent = data.unread_articles;
    document.getElementById("stat-read").textContent = data.read_articles;
    document.getElementById("stat-bookmarked").textContent =
      data.bookmarked_articles;
  } catch (e) {
    console.error("통계 로딩 실패:", e);
  }
}

// === 글 목록 ===
async function loadArticles() {
  const listEl = document.getElementById("article-list");
  listEl.innerHTML = '<div class="loading">로딩 중...</div>';

  try {
    let url = `${API}/api/articles?limit=50`;
    if (currentFilter === "unread") url += "&is_read=false";

    const res = await fetch(url);
    const data = await res.json();
    let articles = data.articles || [];

    if (currentFilter === "bookmarked") {
      articles = articles.filter((a) => a.is_bookmarked);
    }

    if (articles.length === 0) {
      listEl.innerHTML = '<div class="loading">📭 표시할 글이 없습니다.</div>';
      return;
    }

    listEl.innerHTML = articles.map((a) => renderArticleCard(a)).join("");
  } catch (e) {
    listEl.innerHTML =
      '<div class="loading">❌ 로딩 실패. 서버를 확인해주세요.</div>';
    console.error("글 목록 로딩 실패:", e);
  }
}

function renderArticleCard(article) {
  const readClass = article.is_read ? "read" : "";
  const bookmarkIcon = article.is_bookmarked ? "⭐" : "☆";

  const tagsHtml = (article.tags || [])
    .map((t) => `<span class="tag">${t}</span>`)
    .join("");

  const summaryHtml = (article.summary_lines || [])
    .map(
      (line, i) =>
        `<div class="summary-line" data-num="${i + 1}">${line}</div>`,
    )
    .join("");

  return `
        <div class="article-card ${readClass}" id="card-${article.id}">
            <div class="card-header">
                <a class="card-title" href="${article.url}" target="_blank"
                   onclick="markRead(${article.id})">${article.title}</a>
                <div class="card-actions">
                    <button class="btn-small btn-secondary"
                            onclick="toggleBookmark(${article.id})">${bookmarkIcon}</button>
                </div>
            </div>
            <div class="card-meta">
                <span>👤 ${article.author}</span>
                <span>📦 ${article.platform}</span>
                <span>📅 ${formatDate(article.published_at)}</span>
            </div>
            ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ""}
            ${summaryHtml ? `<div class="card-summary">${summaryHtml}</div>` : ""}
        </div>
    `;
}

// === 다이제스트 뷰 ===
async function loadDigest() {
  const digestEl = document.getElementById("digest-view");
  digestEl.innerHTML = '<div class="loading">로딩 중...</div>';

  try {
    const res = await fetch(`${API}/api/digest/latest`);
    const data = await res.json();

    if (!data.digest || data.digest.length === 0) {
      digestEl.innerHTML =
        '<div class="loading">📭 다이제스트가 없습니다. 🔄 새로고침을 눌러 생성하세요.</div>';
      return;
    }

    let html = "";
    let currentCategory = "";

    for (const item of data.digest) {
      if (item.category !== currentCategory) {
        currentCategory = item.category;
        html += `<div class="category-divider">${currentCategory}</div>`;
      }

      const tagsHtml = (item.tags || [])
        .map((t) => {
          const isMatched = (item.matched_tags || []).includes(t);
          return `<span class="tag ${isMatched ? "matched" : ""}">${t}</span>`;
        })
        .join("");

      const summaryHtml = (item.summary_lines || [])
        .map(
          (line, i) =>
            `<div class="summary-line" data-num="${i + 1}">${line}</div>`,
        )
        .join("");

      html += `
                <div class="article-card">
                    <div class="card-header">
                        <a class="card-title" href="${item.url}" target="_blank">${item.title}</a>
                    </div>
                    <div class="card-meta">
                        <span>👤 ${item.author}</span>
                        <span>📦 ${item.platform}</span>
                        <span>🎯 유사도: ${(item.similarity * 100).toFixed(0)}%</span>
                    </div>
                    ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ""}
                    ${summaryHtml ? `<div class="card-summary">${summaryHtml}</div>` : ""}
                </div>
            `;
    }

    digestEl.innerHTML = html;
  } catch (e) {
    digestEl.innerHTML = '<div class="loading">❌ 다이제스트 로딩 실패.</div>';
    console.error("다이제스트 로딩 실패:", e);
  }
}

// === 필터 ===
function setFilter(filter) {
  currentFilter = filter;

  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.remove("active"));
  document.querySelector(`[data-filter="${filter}"]`).classList.add("active");

  const articleList = document.getElementById("article-list");
  const digestView = document.getElementById("digest-view");

  if (filter === "digest") {
    articleList.classList.add("hidden");
    digestView.classList.remove("hidden");
    loadDigest();
  } else {
    articleList.classList.remove("hidden");
    digestView.classList.add("hidden");
    loadArticles();
  }
}

// === 액션 ===
async function markRead(articleId) {
  try {
    await fetch(`${API}/api/articles/${articleId}/read`, { method: "POST" });
    const card = document.getElementById(`card-${articleId}`);
    if (card) card.classList.add("read");
    loadStats();
  } catch (e) {
    console.error("읽음 처리 실패:", e);
  }
}

async function toggleBookmark(articleId) {
  try {
    const res = await fetch(`${API}/api/articles/${articleId}/bookmark`, {
      method: "POST",
    });
    const data = await res.json();
    loadArticles();
    loadStats();
  } catch (e) {
    console.error("북마크 실패:", e);
  }
}

async function runDigest() {
  const btn = document.getElementById("btn-run");
  const statusEl = document.getElementById("pipeline-status");

  btn.disabled = true;
  btn.textContent = "⏳ 실행 중...";
  statusEl.classList.remove("hidden");

  try {
    await fetch(`${API}/api/digest/run`, { method: "POST" });

    // 폴링으로 완료 대기
    const poll = setInterval(async () => {
      const res = await fetch(`${API}/api/digest/status`);
      const status = await res.json();

      if (!status.running) {
        clearInterval(poll);
        btn.disabled = false;
        btn.textContent = "🔄 새로고침";
        statusEl.classList.add("hidden");
        loadStats();
        loadArticles();
      }
    }, 3000);
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "🔄 새로고침";
    statusEl.classList.add("hidden");
    console.error("파이프라인 실행 실패:", e);
  }
}

// === 설정 ===
function toggleSettings() {
  document.getElementById("settings-panel").classList.toggle("hidden");
}

async function loadTags() {
  try {
    const res = await fetch(`${API}/api/settings/tags`);
    const data = await res.json();
    const tags = (data.tags || []).map((t) => t.tag);
    document.getElementById("tags-input").value = tags.join(", ");
  } catch (e) {
    console.error("태그 로딩 실패:", e);
  }
}

async function saveTags() {
  const input = document.getElementById("tags-input").value;
  const tags = input
    .split(",")
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);

  try {
    await fetch(`${API}/api/settings/tags`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tags }),
    });
    alert("✅ 관심 태그가 저장되었습니다.");
  } catch (e) {
    alert("❌ 저장 실패");
    console.error("태그 저장 실패:", e);
  }
}

// === 유틸 ===
function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

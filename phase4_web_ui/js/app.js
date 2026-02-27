/**
 * App: form submit, loading/error/results UI.
 */

import { API_BASE } from "./config.js";
import { buildRecommendRequest, fetchRecommend, parseRecommendResponse } from "./api.js";

const form = document.getElementById("preferences-form");
const submitBtn = document.getElementById("submit-btn");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const errorMessage = document.getElementById("error-message");
const resultsEl = document.getElementById("results");
const summaryBlock = document.getElementById("summary-block");
const summaryText = document.getElementById("summary-text");
const resultsCount = document.getElementById("results-count");
const restaurantsList = document.getElementById("restaurants-list");
const noResultsEl = document.getElementById("no-results");

function hideAllFeedback() {
  loadingEl.setAttribute("hidden", "");
  errorEl.setAttribute("hidden", "");
  resultsEl.setAttribute("hidden", "");
  summaryBlock.setAttribute("hidden", "");
  noResultsEl.setAttribute("hidden", "");
}

function showLoading() {
  hideAllFeedback();
  loadingEl.removeAttribute("hidden");
  submitBtn.disabled = true;
}

function showError(message) {
  hideAllFeedback();
  errorMessage.textContent = message;
  errorEl.removeAttribute("hidden");
  submitBtn.disabled = false;
}

function showResults(parsed) {
  hideAllFeedback();
  resultsEl.removeAttribute("hidden");

  if (parsed.summary) {
    summaryText.textContent = parsed.summary;
    summaryBlock.removeAttribute("hidden");
  } else {
    summaryBlock.setAttribute("hidden", "");
  }

  const list = parsed.restaurants || [];
  resultsCount.textContent = list.length === 0 ? "No restaurants found" : `${list.length} restaurant${list.length === 1 ? "" : "s"}`;

  if (list.length === 0) {
    noResultsEl.removeAttribute("hidden");
    restaurantsList.innerHTML = "";
  } else {
    noResultsEl.setAttribute("hidden", "");
    restaurantsList.innerHTML = list.map(renderRestaurantCard).join("");
  }

  submitBtn.disabled = false;
}

/**
 * @param {import("./types.js").RecommendResponse["restaurants"][0]} r
 * @returns {string} HTML string
 */
function renderRestaurantCard(r) {
  const name = escapeHtml(String(r.name ?? "Unnamed"));
  const location = escapeHtml(String(r.location ?? ""));
  const rate = r.rate != null ? String(r.rate) : "—";
  const cost = r.cost_for_two != null ? `₹${Number(r.cost_for_two).toLocaleString("en-IN")}` : "—";
  const cuisines = escapeHtml(String(r.cuisines ?? ""));
  const url = r.url ? escapeAttr(r.url) : "";
  const linkOpen = url ? `<a href="${url}" target="_blank" rel="noopener">` : "";
  const linkClose = url ? "</a>" : "";

  return `
    <article class="restaurant-card">
      <h3 class="restaurant-name">${linkOpen}${name}${linkClose}</h3>
      <p class="restaurant-meta">${location} · Rating ${rate}/5 · ${cost} for two</p>
      ${cuisines ? `<p class="restaurant-cuisines">${cuisines}</p>` : ""}
    </article>
  `;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function escapeAttr(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML.replace(/"/g, "&quot;");
}

function getFormData() {
  const fd = new FormData(form);
  return Object.fromEntries(
    Array.from(fd.entries()).map(([k, v]) => [k, v instanceof File ? "" : String(v)])
  );
}

async function loadLocationOptions() {
  const select = document.getElementById("location");
  if (!select) return;
  const base = API_BASE.replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/locations`);
    if (!res.ok) return;
    const data = await res.json();
    const locations = Array.isArray(data.locations) ? data.locations : [];
    locations.forEach((loc) => {
      const opt = document.createElement("option");
      opt.value = loc;
      opt.textContent = loc;
      select.appendChild(opt);
    });
  } catch (_) {
    // Offline or old API: leave only "Any"
  }
}

loadLocationOptions();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = getFormData();
  const body = buildRecommendRequest(formData);
  showLoading();

  try {
    const data = await fetchRecommend(body);
    const parsed = parseRecommendResponse(data);
    showResults(parsed);
  } catch (err) {
    showError(err instanceof Error ? err.message : String(err));
  }
});

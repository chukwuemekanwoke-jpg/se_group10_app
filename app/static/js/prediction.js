// Prediction module for bike availability forecasting

function initPredictionUI() {
  const predictBtn = document.getElementById("predictBtn");
  const predictDate = document.getElementById("predictDate");
  const predictTime = document.getElementById("predictTime");
  const predictionResult = document.getElementById("predictionResult");

  if (!predictBtn) return;

  predictBtn.addEventListener("click", async () => {
    await handlePredictionRequest(predictDate, predictTime, predictionResult);
  });
}

async function handlePredictionRequest(predictDate, predictTime, predictionResult) {
  const dateValue = predictDate.value;
  const timeValue = predictTime.value;

  // Validation
  if (!window.selectedStation) {
    predictionResult.textContent = "Please select a station on the map first.";
    return;
  }

  if (!dateValue || !timeValue) {
    predictionResult.textContent = "Please choose both date and time.";
    return;
  }

  // Show loading state
  predictionResult.textContent = `Preparing prediction for ${window.selectedStation.name} at ${dateValue} ${timeValue}...`;

  try {
    const predictionData = await fetchPrediction(
      window.selectedStation.number,
      dateValue,
      timeValue
    );
    displayPredictionResult(predictionData, predictionResult);
  } catch (err) {
    console.error("Prediction error:", err);
    predictionResult.textContent = "Prediction unavailable right now.";
  }
}

async function fetchPrediction(stationId, date, time) {
  const url = `/api/predict?station_id=${stationId}&date=${date}&time=${time}`;
  
  const resp = await fetch(url);

  if (!resp.ok) {
    throw new Error(`Prediction request failed with status ${resp.status}`);
  }

  return await resp.json();
}

function displayPredictionResult(data, resultPanel) {
  const bikes = parseInt(data.predicted_bikes, 10) || 0;

  // Colour + label based on availability level
  let color, badgeBg, badgeColor, statusLabel;
  if (bikes >= 10) {
    color       = "#16a34a";
    badgeBg     = "#dcfce7";
    badgeColor  = "#15803d";
    statusLabel = "High availability";
  } else if (bikes >= 5) {
    color       = "#d97706";
    badgeBg     = "#fef3c7";
    badgeColor  = "#b45309";
    statusLabel = "Moderate availability";
  } else {
    color       = "#dc2626";
    badgeBg     = "#fee2e2";
    badgeColor  = "#b91c1c";
    statusLabel = "Low availability";
  }

  // Bar fill: assume station capacity ~30 as fallback max for visual
  const pct = Math.min(100, Math.round((bikes / 30) * 100));

  // Format date nicely if possible
  let niceDate = data.date;
  try {
    niceDate = new Date(data.date + "T00:00:00").toLocaleDateString("en-IE", {
      weekday: "short", day: "numeric", month: "short", year: "numeric"
    });
  } catch (_) {}

  resultPanel.innerHTML = `
    <div class="pred-card">
      <div class="pred-header">
        <!-- Wheel icon (Troithean) -->
        <svg class="pred-header-icon" viewBox="0 0 24 24" fill="none"
             stroke="white" stroke-width="1.75" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/>
          <circle cx="12" cy="12" r="2" fill="white" stroke="none"/>
          <line x1="12" y1="12" x2="12" y2="2"/>
          <line x1="12" y1="12" x2="20.66" y2="7"/>
          <line x1="12" y1="12" x2="20.66" y2="17"/>
          <line x1="12" y1="12" x2="12" y2="22"/>
          <line x1="12" y1="12" x2="3.34" y2="17"/>
          <line x1="12" y1="12" x2="3.34" y2="7"/>
        </svg>
        <span class="pred-header-title">Availability Forecast</span>
      </div>
      <div class="pred-body" style="--pred-color:${color};--pred-badge-bg:${badgeBg};--pred-badge-color:${badgeColor}">
        <div class="pred-station-name">${data.station_name}</div>
        <div class="pred-datetime-tag">${niceDate} &middot; ${data.time}</div>

        <div class="pred-count-row">
          <span class="pred-big-num">${bikes}</span>
          <span class="pred-count-label">predicted<br>available bikes</span>
        </div>

        <div class="pred-bar-track">
          <div class="pred-bar-fill" style="width:${pct}%"></div>
        </div>
        <div class="pred-bar-meta">
          <span>0</span>
          <span>${bikes} of ~30 capacity</span>
        </div>

        <div class="pred-status-badge">
          <span class="pred-dot"></span>
          ${statusLabel}
        </div>
      </div>
    </div>
  `;
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initPredictionUI();
});

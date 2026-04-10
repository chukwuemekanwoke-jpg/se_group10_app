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
  resultPanel.innerHTML = `
    <div class="prediction-result">
      <div class="prediction-item">
        <strong>Station:</strong> ${data.station_name}
      </div>
      <div class="prediction-item">
        <strong>Date:</strong> ${data.date}
      </div>
      <div class="prediction-item">
        <strong>Time:</strong> ${data.time}
      </div>
      <div class="prediction-item highlight">
        <strong>Predicted available bikes:</strong> <span class="bike-count">${data.predicted_bikes}</span>
      </div>
    </div>
  `;
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initPredictionUI();
});

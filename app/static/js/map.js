let map;
let markers = [];
let infoWindow;

let mergedStations = [];
let userMarker = null;
let userCircle = null;
let userPosition = null;

function initMap() {
  const dublin = { lat: 53.3498, lng: -6.2603 };

  map = new google.maps.Map(document.getElementById("map"), {
    center: dublin,
    zoom: 13,
  });

  infoWindow = new google.maps.InfoWindow();

  wireUiActions();
  loadStationsAndAvailability();
  loadWeather();

  setInterval(loadWeather, 10 * 60 * 1000); // refresh weather every 10 minutes
}

// Ensure Google callback can see initMap
window.initMap = initMap;

function wireUiActions() {
  const refreshBtn = document.getElementById("refreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Refreshing...";
      try {
        await Promise.all([loadStationsAndAvailability(), loadWeather()]);
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh";
      }
    });
  }

  const locateBtn = document.getElementById("locateBtn");
  if (locateBtn) {
    locateBtn.addEventListener("click", getUserLocation);
  }

  const findRouteBtn = document.getElementById("findRouteBtn");
  if (findRouteBtn) {
    findRouteBtn.addEventListener("click", findNearestStation);
  }
}

async function loadStationsAndAvailability() {
  try {
    const [stationsResp, latestResp] = await Promise.all([
      fetch("/api/stations"),
      fetch("/api/latest"),
    ]);

    if (!stationsResp.ok) throw new Error("Failed to fetch /api/stations");
    if (!latestResp.ok) throw new Error("Failed to fetch /api/latest");

    const stations = await stationsResp.json();
    const latest = await latestResp.json();

    const latestByNumber = new Map();
    for (const row of latest) {
      latestByNumber.set(row.number, row);
    }

    const merged = stations.map((s) => {
      const stationNumber = s.number;
      return {
        ...s,
        latest: latestByNumber.get(stationNumber) || null,
      };
    });

    mergedStations = merged;
    renderMarkers(mergedStations);
  } catch (err) {
    console.error(err);
    const panel = document.getElementById("stationDetails");
    if (panel) panel.textContent = "Error loading station data.";
  }
}

function clearMarkers() {
  for (const m of markers) m.setMap(null);
  markers = [];
}

function renderMarkers(stations) {
  clearMarkers();

  for (const s of stations) {
    const lat = parseFloat(s.position_lat);
    const lng = parseFloat(s.position_lng);

    if (Number.isNaN(lat) || Number.isNaN(lng)) continue;

    const bikes = s.latest?.available_bikes;
    const stands = s.latest?.available_bike_stands;
    const status = s.latest?.status;

    const capacity = s.bike_stands;
    const { icon } = computeMarkerStyle(bikes, stands, capacity, status);

    const marker = new google.maps.Marker({
      position: { lat, lng },
      map,
      title: s.name || `Station ${s.number}`,
      icon,
    });

    marker.addListener("click", () => {
      showStationInfo(marker, s);
    });

    markers.push(marker);
  }
}

function computeMarkerStyle(bikes, stands, capacity, status) {
  let fillColor = "#808080";
  if (status && status !== "OPEN") fillColor = "#666666";

  if (typeof bikes === "number") {
    if (bikes === 0) fillColor = "#d9534f";
    else if (bikes <= 5) fillColor = "#f0ad4e";
    else fillColor = "#5cb85c";
  }

  let scale = 7;

  if (
    typeof bikes === "number" &&
    typeof stands === "number" &&
    typeof capacity === "number" &&
    capacity > 0
  ) {
    const occupiedPct = bikes / capacity;
    scale = 6 + Math.round(occupiedPct * 8);
  }

  return {
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor,
      fillOpacity: 0.9,
      strokeWeight: 1,
      scale,
    },
  };
}

function showStationInfo(marker, station) {
  const latest = station.latest;

  const bikes = latest?.available_bikes;
  const stands = latest?.available_bike_stands;
  const status = latest?.status || "UNKNOWN";
  const lastUpdate = latest?.last_update || "N/A";

  const name = station.name || `Station ${station.number}`;
  const address = station.address || "";

  const html = `
    <div style="min-width:220px">
      <strong>${name}</strong><br/>
      ${address ? `${address}<br/>` : ""}
      <div><strong>Status:</strong> ${status}</div>
      <div><strong>Bikes:</strong> ${bikes ?? "?"}</div>
      <div><strong>Stands:</strong> ${stands ?? "?"}</div>
      <div style="font-size:12px; opacity:0.8"><strong>Updated:</strong> ${lastUpdate}</div>
    </div>
  `;

  infoWindow.setContent(html);
  infoWindow.open(map, marker);

  const panel = document.getElementById("stationDetails");
  if (panel) panel.innerHTML = html;
}

async function loadWeather() {
  const panel = document.getElementById("weatherDetails");
  if (panel) panel.textContent = "Loading weather...";

  try {
    const resp = await fetch("/api/weather/latest");
    if (!resp.ok) throw new Error("Failed to fetch /api/weather/latest");

    const w = await resp.json();

    const city = w.city_name ?? "Dublin";
    const desc = w.weather_desc ?? "";
    const main = w.weather_main ?? "";
    const temp = typeof w.temp === "number" ? w.temp.toFixed(1) : w.temp;
    const feels = typeof w.feels_like === "number" ? w.feels_like.toFixed(1) : w.feels_like;
    const wind = typeof w.wind_speed === "number" ? w.wind_speed.toFixed(1) : w.wind_speed;
    const hum = w.humidity;
    const updated = w.dt_utc ?? "";

    const iconCode = w.weather_icon;
    const iconUrl = iconCode
      ? `https://openweathermap.org/img/wn/${iconCode}@2x.png`
      : null;

    const rain = w.rain_1h;
    const snow = w.snow_1h;

    const extraPrecip = [];
    if (typeof rain === "number") extraPrecip.push(`Rain (1h): ${rain} mm`);
    if (typeof snow === "number") extraPrecip.push(`Snow (1h): ${snow} mm`);

    if (!panel) return;

    panel.innerHTML = `
      <div style="display:flex; gap:10px; align-items:center;">
        ${iconUrl ? `<img src="${iconUrl}" alt="${desc || main}" style="width:48px;height:48px;">` : ""}
        <div>
          <div><strong>${city}</strong></div>
          <div>${main}${desc ? ` — ${desc}` : ""}</div>
        </div>
      </div>

      <div style="margin-top:10px">
        <div><strong>Temp:</strong> ${temp}°C</div>
        <div><strong>Feels like:</strong> ${feels}°C</div>
        <div><strong>Humidity:</strong> ${hum}%</div>
        <div><strong>Wind:</strong> ${wind} m/s</div>
        ${extraPrecip.length ? `<div style="margin-top:6px">${extraPrecip.map(x => `<div>${x}</div>`).join("")}</div>` : ""}
        <div style="font-size:12px;opacity:.8;margin-top:8px"><strong>Updated:</strong> ${updated}</div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    if (panel) panel.textContent = "Weather unavailable.";
  }
}

function getUserLocation() {
  const resultPanel = document.getElementById("routeResult");
  if (resultPanel) resultPanel.textContent = "Getting your location...";

  if (!navigator.geolocation) {
    if (resultPanel) resultPanel.textContent = "Geolocation is not supported by your browser.";
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      userPosition = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      showUserLocation();
      if (resultPanel) resultPanel.textContent = "Location captured. Now click 'Find nearest station'.";
    },
    () => {
      if (resultPanel) resultPanel.textContent = "Unable to retrieve your location.";
    }
  );
}

function showUserLocation() {
  const radius = getSelectedRadius();

  if (userMarker) userMarker.setMap(null);
  if (userCircle) userCircle.setMap(null);

  userMarker = new google.maps.Marker({
    position: userPosition,
    map,
    title: "Your location",
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor: "#2563eb",
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: 2,
      scale: 8,
    },
  });

  userCircle = new google.maps.Circle({
    strokeColor: "#2563eb",
    strokeOpacity: 0.8,
    strokeWeight: 2,
    fillColor: "#93c5fd",
    fillOpacity: 0.2,
    map,
    center: userPosition,
    radius,
  });

  map.panTo(userPosition);
  map.setZoom(14);
}

function getSelectedRadius() {
  const radiusSelect = document.getElementById("radiusSelect");
  return Number(radiusSelect?.value || 800);
}

function findNearestStation() {
  const resultPanel = document.getElementById("routeResult");

  if (!userPosition) {
    if (resultPanel) resultPanel.textContent = "Please click 'Use my location' first.";
    return;
  }

  if (!mergedStations.length) {
    if (resultPanel) resultPanel.textContent = "Station data is not loaded yet.";
    return;
  }

  const radius = getSelectedRadius();
  showUserLocation();

  const allSuitableStations = mergedStations
    .map((station) => {
      const lat = parseFloat(station.position_lat);
      const lng = parseFloat(station.position_lng);

      if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

      const distance = haversineDistanceMeters(
        userPosition.lat,
        userPosition.lng,
        lat,
        lng
      );

      return {
        ...station,
        _distance: distance,
      };
    })
    .filter((station) => {
      if (!station) return false;
      const bikes = station.latest?.available_bikes ?? 0;
      const status = station.latest?.status ?? "UNKNOWN";
      return status === "OPEN" && bikes > 0;
    })
    .sort((a, b) => a._distance - b._distance);

  if (!allSuitableStations.length) {
    if (resultPanel) {
      resultPanel.innerHTML = `
        <strong>No available station found</strong><br/>
        There are currently no open stations with available bikes.
      `;
    }
    return;
  }

  const inRadius = allSuitableStations.filter((station) => station._distance <= radius);

  const best = inRadius.length ? inRadius[0] : allSuitableStations[0];
  const usedFallback = inRadius.length === 0;

  const destination = {
    lat: parseFloat(best.position_lat),
    lng: parseFloat(best.position_lng),
  };

  const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${userPosition.lat},${userPosition.lng}&destination=${destination.lat},${destination.lng}&travelmode=walking`;

  if (resultPanel) {
    resultPanel.innerHTML = `
      ${usedFallback ? `<div style="margin-bottom:8px; color:#7c2d12; font-weight:700;">No suitable station within ${radius} m. Showing nearest available station instead.</div>` : ""}
      <strong>Recommended station:</strong><br/>
      ${best.name || `Station ${best.number}`}<br/>
      ${best.address || ""}<br/><br/>
      <strong>Distance:</strong> ${Math.round(best._distance)} m<br/>
      <strong>Available bikes:</strong> ${best.latest?.available_bikes ?? "?"}<br/>
      <strong>Free stands:</strong> ${best.latest?.available_bike_stands ?? "?"}<br/><br/>
      <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a>
    `;
  }

  map.panTo(destination);
}

function haversineDistanceMeters(lat1, lng1, lat2, lng2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371000;

  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
let map;
let markers = [];
let infoWindow;

function initMap() {
  const dublin = { lat: 53.3498, lng: -6.2603 };

  map = new google.maps.Map(document.getElementById("map"), {
    center: dublin,
    zoom: 13,
  });

  infoWindow = new google.maps.InfoWindow();

  loadStationsAndAvailability();
  loadWeather();
  setInterval(loadWeather, 10 * 60 * 1000); // refresh every 10 minutes
}

// Ensure Google callback can see initMap
window.initMap = initMap;

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

    // Map latest availability by station number
    const latestByNumber = new Map();
    for (const row of latest) {
      latestByNumber.set(row.number, row);
    }

    // Merge: station metadata + latest availability
    const merged = stations.map((s) => {
      const stationNumber = s.number; // adjust if your stations use a different field name
      return {
        ...s,
        latest: latestByNumber.get(stationNumber) || null,
      };
    });

    renderMarkers(merged);
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
    // Your stations endpoint likely uses these names (adjust if needed)
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
  // Colour encoding by bike availability
  let fillColor = "#808080"; // default grey (unknown)
  if (status && status !== "OPEN") fillColor = "#666666"; // closed-ish

  if (typeof bikes === "number") {
    if (bikes === 0) fillColor = "#d9534f";        // red
    else if (bikes <= 5) fillColor = "#f0ad4e";    // orange
    else fillColor = "#5cb85c";                    // green
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

    // OpenWeather icon URL (standard)
    const iconCode = w.weather_icon;
    const iconUrl = iconCode
      ? `https://openweathermap.org/img/wn/${iconCode}@2x.png`
      : null;

    const rain = w.rain_1h; // may be null
    const snow = w.snow_1h; // may be null

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
let map;

function initMap() {
    const dublin = { lat: 53.3498, lng: -6.2603 };

    map = new google.maps.Map(document.getElementById("map"), {
        center: dublin,
        zoom: 13
    });

    loadStations();
}

async function loadStations() {
    const response = await fetch("/api/stations");
    const stations = await response.json();

    stations.forEach(station => {
        new google.maps.Marker({
            position: {
                lat: parseFloat(station.position_lat),
                lng: parseFloat(station.position_lng)
            },
            map: map,
            title: station.name
        });
    });
}
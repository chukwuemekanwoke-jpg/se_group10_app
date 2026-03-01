// main.js - Frontend JavaScript
// This is where you call your Flask API routes and update the page

// Example: Fetch live bike data from Flask
fetch('/api/bikes/live')
    .then(response => response.json())
    .then(data => {
        console.log('Live bike data:', data);
        // TODO: Display on map or table
    })
    .catch(error => console.error('Error fetching bike data:', error));

// Example: Fetch current weather
fetch('/api/weather')
    .then(response => response.json())
    .then(data => {
        console.log('Weather:', data);
        // TODO: Display weather info on page
    })
    .catch(error => console.error('Error fetching weather:', error));

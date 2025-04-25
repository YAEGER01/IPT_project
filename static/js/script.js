function updateDateTime() {
    fetch('/get-time')
        .then(response => response.json())
        .then(data => {
            document.getElementById('current-time').textContent = "Date & Time: " + data.time;
        })
        .catch(error => console.error('Error fetching time:', error));
}


updateDateTime();
setInterval(updateDateTime, 1000);
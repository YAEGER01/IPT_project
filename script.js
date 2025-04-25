// Function para sa PH Time Zone mga pipol
function updateDateTime() {
    var now = new Date();

    // pagkuha ng date and time
    var options = {
        timeZone: 'Asia/Manila',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true // gagamitan ng PH time
    };

    var dateTime = now.toLocaleString('en-PH', options);


    document.getElementById('current-time').textContent = "Date & Time: " + dateTime;
}


updateDateTime();
setInterval(updateDateTime, 1000);
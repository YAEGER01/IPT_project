
$('#refreshListBtn').click(function (event) {
    event.preventDefault();

    $.ajax({
        url: "{{ url_for('admin_dashboard') }}",  // URL to refresh the dashboard content
        type: "GET",
        success: function (response) {

            $('#instructorList').html(response.instructors_html);
            $('#studentList').html(response.students_html);


            const instructorRows = document.querySelectorAll("#instructorList tr");
            const studentRows = document.querySelectorAll("#studentList tr");

            searchBar.addEventListener("input", function () {
                const filter = searchBar.value.toLowerCase();


                instructorRows.forEach(row => {
                    const name = row.cells[0]?.textContent.toLowerCase();
                    const email = row.cells[1]?.textContent.toLowerCase();
                    if (name && email && (name.includes(filter) || email.includes(filter))) {
                        row.style.display = "";
                    } else {
                        row.style.display = "none";
                    }
                });


                studentRows.forEach(row => {
                    const name = row.cells[0]?.textContent.toLowerCase();
                    const email = row.cells[1]?.textContent.toLowerCase();
                    if (name && email && (name.includes(filter) || email.includes(filter))) {
                        row.style.display = "";
                    } else {
                        row.style.display = "none";
                    }
                });
            });
        },
        error: function () {
            alert('Error refreshing the lists.');
        }
    });
});


const addInstructorModal = document.getElementById("addInstructorModal");
const listsModal = document.getElementById("listsModal");
const closeAddInstructorModal = document.getElementById("closeAddInstructorModal");
const closeChangePasswordModal = document.getElementById("closeChangePasswordModal");
const closeListsModal = document.getElementById("closeListsModal");
const addInstructorBtn = document.getElementById("addInstructorBtn");
const changePasswordBtn = document.getElementById("changePasswordBtn");
const generateReportsBtn = document.getElementById("generateReportsBtn");


addInstructorBtn.onclick = function () { addInstructorModal.style.display = "block"; }
changePasswordBtn.onclick = function () { changePasswordModal.style.display = "block"; }
generateReportsBtn.onclick = function () { listsModal.style.display = "block"; }


closeAddInstructorModal.onclick = function () { addInstructorModal.style.display = "none"; }
closeChangePasswordModal.onclick = function () { changePasswordModal.style.display = "none"; }
closeListsModal.onclick = function () { listsModal.style.display = "none"; }


window.onclick = function (event) {
    if (event.target === addInstructorModal) { addInstructorModal.style.display = "none"; }
    if (event.target === changePasswordModal) { changePasswordModal.style.display = "none"; }
    if (event.target === listsModal) { listsModal.style.display = "none"; }
}


const searchBar = document.getElementById("searchBar");
const instructorRows = document.querySelectorAll("#instructorList tr");
const studentRows = document.querySelectorAll("#studentList tr");

searchBar.addEventListener("input", function () {
    const filter = searchBar.value.toLowerCase();


    instructorRows.forEach(row => {
        const name = row.cells[0]?.textContent.toLowerCase();
        const email = row.cells[1]?.textContent.toLowerCase();
        if (name && email && (name.includes(filter) || email.includes(filter))) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });


    studentRows.forEach(row => {
        const name = row.cells[0]?.textContent.toLowerCase();
        const email = row.cells[1]?.textContent.toLowerCase();
        if (name && email && (name.includes(filter) || email.includes(filter))) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
});


function openInstructorModal(instructorId, fullName, email) {
    document.getElementById('instructor_id').textContent = instructorId;
    document.getElementById('instructor_full_name').textContent = fullName;
    document.getElementById('instructor_email').textContent = email;
    new bootstrap.Modal(document.getElementById('instructorModal')).show();
}


document.querySelector('.delete-btn').addEventListener('click', () => {
    const userId = document.querySelector('.delete-input').value.trim();

    if (!userId) {
        alert("Please enter a User ID to delete.");
        return;
    }

    if (!confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
        return;
    }


    fetch('/delete_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.status === 'success') {
                document.querySelector('.delete-input').value = '';

            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the user.');
        });
});


$(document).on('click', '#generateReportsBtn', function () {
    $('#listsModal').show();
});

function updateCounts() {
    fetch('/admin_dashboard', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {

            document.getElementById('instructorCount').textContent = data.instructor_count;
            document.getElementById('studentCount').textContent = data.student_count;
            document.getElementById('adminCount').textContent = data.admin_count;
        })
        .catch(error => console.error('Error fetching counts:', error));
}

// Update counts every 5 seconds
setInterval(updateCounts, 5000);

function fetchLiveCounts() {

    $.ajax({
        url: '{{ url_for("admin_dashboard") }}',
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            // Update the counts on the page
            $('#instructor_count').text(data.instructor_count);
            $('#student_count').text(data.student_count);
            $('#admin_count').text(data.admin_count);

            // Update the instructors and students lists
            $('#instructors_list').html(data.instructor_list_html);
            $('#students_list').html(data.student_list_html);
        }
    });
}


setInterval(fetchLiveCounts, 5000); // Refresh every 5 seconds
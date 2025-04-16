// Refresh the instructor and student lists using AJAX
$('#refreshListBtn').click(function (event) {
    event.preventDefault();  // Prevent the form from submitting normally

    $.ajax({
        url: "{{ url_for('admin_dashboard') }}",  // URL to refresh the dashboard content
        type: "GET",
        success: function (response) {
            // Replace the current content in the modal lists with the new data
            $('#instructorList').html(response.instructors_html);
            $('#studentList').html(response.students_html);

            // Rebind the search functionality after refreshing the list
            const instructorRows = document.querySelectorAll("#instructorList tr");
            const studentRows = document.querySelectorAll("#studentList tr");

            searchBar.addEventListener("input", function () {
                const filter = searchBar.value.toLowerCase();

                // Filter Instructor List
                instructorRows.forEach(row => {
                    const name = row.cells[0]?.textContent.toLowerCase();
                    const email = row.cells[1]?.textContent.toLowerCase();
                    if (name && email && (name.includes(filter) || email.includes(filter))) {
                        row.style.display = "";
                    } else {
                        row.style.display = "none";
                    }
                });

                // Filter Student List
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

// Modal show/hide functionality
const addInstructorModal = document.getElementById("addInstructorModal");
const listsModal = document.getElementById("listsModal");
const closeAddInstructorModal = document.getElementById("closeAddInstructorModal");
const closeChangePasswordModal = document.getElementById("closeChangePasswordModal");
const closeListsModal = document.getElementById("closeListsModal");
const addInstructorBtn = document.getElementById("addInstructorBtn");
const changePasswordBtn = document.getElementById("changePasswordBtn");
const generateReportsBtn = document.getElementById("generateReportsBtn");

// Show modals
addInstructorBtn.onclick = function () { addInstructorModal.style.display = "block"; }
changePasswordBtn.onclick = function () { changePasswordModal.style.display = "block"; }
generateReportsBtn.onclick = function () { listsModal.style.display = "block"; }

// Close modals
closeAddInstructorModal.onclick = function () { addInstructorModal.style.display = "none"; }
closeChangePasswordModal.onclick = function () { changePasswordModal.style.display = "none"; }
closeListsModal.onclick = function () { listsModal.style.display = "none"; }

// Close modals if clicked outside
window.onclick = function (event) {
    if (event.target === addInstructorModal) { addInstructorModal.style.display = "none"; }
    if (event.target === changePasswordModal) { changePasswordModal.style.display = "none"; }
    if (event.target === listsModal) { listsModal.style.display = "none"; }
}

// Search filter functionality
const searchBar = document.getElementById("searchBar");
const instructorRows = document.querySelectorAll("#instructorList tr");
const studentRows = document.querySelectorAll("#studentList tr");

searchBar.addEventListener("input", function () {
    const filter = searchBar.value.toLowerCase();

    // Filter Instructor List
    instructorRows.forEach(row => {
        const name = row.cells[0]?.textContent.toLowerCase();
        const email = row.cells[1]?.textContent.toLowerCase();
        if (name && email && (name.includes(filter) || email.includes(filter))) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });

    // Filter Student List
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

// Open instructor modal with data
function openInstructorModal(instructorId, fullName, email) {
    document.getElementById('instructor_id').textContent = instructorId;
    document.getElementById('instructor_full_name').textContent = fullName;
    document.getElementById('instructor_email').textContent = email;
    new bootstrap.Modal(document.getElementById('instructorModal')).show();
}

// Delete user functionality
document.querySelector('.delete-btn').addEventListener('click', () => {
    const userId = document.querySelector('.delete-input').value.trim();

    if (!userId) {
        alert("Please enter a User ID to delete.");
        return;
    }

    if (!confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
        return;
    }

    // Send AJAX request to backend to delete the user
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
                // Optionally refresh the page or update the UI
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the user.');
        });
});

// Open lists modal
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
            // Update the live counts on the page with the new values
            document.getElementById('instructorCount').textContent = data.instructor_count;
            document.getElementById('studentCount').textContent = data.student_count;
            document.getElementById('adminCount').textContent = data.admin_count;
        })
        .catch(error => console.error('Error fetching counts:', error));
}

// Update counts every 5 seconds
setInterval(updateCounts, 5000);

function fetchLiveCounts() {
    // Send an AJAX request to get the updated counts and lists
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
            $('#instructors_list').html(data.instructors_html);
            $('#students_list').html(data.students_html);
        }
    });
}

// Set an interval to refresh the live counts every few seconds
setInterval(fetchLiveCounts, 5000); // Refresh every 5 seconds
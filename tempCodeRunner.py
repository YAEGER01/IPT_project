from datetime import datetime
from flask import app, redirect, render_template, session, url_for
import pytz

from app import get_db_connection


subject_schedule = {
    "Monday": [
        ("Information Management | IT 221 | 10:00AM - 1:00PM", 10, 13),
        ("Cybersecurity | IT NS 1 | 8:00AM - 10:00AM", 8, 10),
    ],
    "Tuesday": [
        ("Networking 1 | IT 222 | 8:00AM - 10:00AM", 8, 10),
        ("Life and Works of Rizal | GEC 9 | 1:00PM - 2:30PM", 13, 14.5),
    ],
    "Wednesday": [
        ("Quantitative Methods | IT 223 | 2:30PM - 4:00PM", 14.5, 16),
    ],
    "Thursday": [
        ("Accounting for Information Technology | IT 225 | 4:00PM - 5:30PM", 16, 17.5),
        ("The Entrepreneurial Mind | IT GE ELECTIVE 4 | 1:00PM - 3:00PM", 13, 15),
    ],
    "Friday": [
        ("PATHFIT 4 | PE 4 | 1:00PM - 3:00PM", 13, 15),
        ("Integrative Programming and Technologies | IT 224 | 8:00AM - 10:00AM", 8, 10),
    ],
    "Saturday": [
         ("Contemporary World | GEC 6 | 8:30AM - 11:30AM", 8.5, 11.5),
        ("Computer Programming 1 | IT 101 | 12:00PM - 1:00PM", 12, 13),
        ("Computer Programming 1 | IT 101 | 2:00PM - 4:00PM", 14, 16),
    ],
    "Sunday": [
        ("Contemporary World | GEC 6 | 9:00AM - 11:30AM", 9, 11.5),
        ("Introduction to Computing | IT 100 | 1:00PM - 3:00PM", 13, 15),
    ]
}

@app.route("/dashboard")
def dashboard():
    if 'role' in session and session['role'] == 'student':
        user_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(""" 
            SELECT u.name, u.school_id, s.firstname, s.lastname, u.email 
            FROM users u 
            JOIN students s ON u.id = s.user_id 
            WHERE u.id = %s
        """, (user_id,))

        student = cursor.fetchone()
        connection.close()

        if student:
            # Sample subject schedule (24-hour format)
            subject_schedule = {
                "Monday": [
                    ("Information Management | IT 221 | 10:00AM - 1:00PM", 10, 13),
                    ("Cybersecurity | IT NS 1 | 8:00AM - 10:00AM", 8, 10),
                ],
                "Tuesday": [
                    ("Networking 1 | IT 222 | 8:00AM - 10:00AM", 8, 10),
                    ("Life and Works of Rizal | GEC 9 | 1:00PM - 2:30PM", 13, 14.5),
                ],
                "Wednesday": [
                    ("Quantitative Methods | IT 223 | 2:30PM - 4:00PM", 14.5, 16),
                ],
                "Thursday": [
                    ("Accounting for Information Technology | IT 225 | 4:00PM - 5:30PM", 16, 17.5),
                    ("The Entrepreneurial Mind | IT GE ELECTIVE 4 | 1:00PM - 3:00PM", 13, 15),
                ],
                "Friday": [
                    ("PATHFIT 4 | PE 4 | 1:00PM - 3:00PM", 13, 15),
                    ("Integrative Programming and Technologies | IT 224 | 8:00AM - 10:00AM", 8, 10),
                ],
                "Saturday": [
                    ("Contemporary World | GEC 6 | 8:30AM - 11:30AM", 8.5, 11.5),
                    ("Computer Programming 1 | IT 101 | 12:00PM - 1:00PM", 12, 13),
                    ("Computer Programming 1 | IT 101 | 2:00PM - 4:00PM", 14, 16),
                ],
                "Sunday": [
                    ("Contemporary World | GEC 6 | 9:00AM - 11:30AM", 9, 11.5),
                    ("Introduction to Computing | IT 100 | 1:00PM - 3:00PM", 13, 15),
                ]
            }

            # Get current time in PH timezone
            timezone = pytz.timezone("Asia/Manila")
            now = datetime.now(timezone)
            current_day = now.strftime("%A")
            current_hour = now.hour + now.minute / 60

            active_subjects = []
            today_schedule = subject_schedule.get(current_day, [])

            for subject in today_schedule:
                subject_name, start_time, end_time = subject
                if start_time <= current_hour <= end_time:
                    # On time (class is ongoing)
                    status = 'on_time'
                elif current_hour > end_time:
                    # Late (class is over)
                    status = 'late'
                else:
                    # Before the class starts (no interaction yet)
                    status = 'upcoming'

                active_subjects.append({
                    'subject_name': subject_name,
                    'status': status  # 'on_time', 'late', 'upcoming'
                })

            return render_template(
                "dashboard.html", 
                student_name=student['name'], 
                student_id=student['school_id'],
                user=student,  # Pass the full student object for editing
                active_subjects=active_subjects  # Pass active subjects to display on dashboard
            )
        else:
            return "Student not found", 404
    else:
        return redirect(url_for('login'))
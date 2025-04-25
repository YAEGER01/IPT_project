from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
import os
import string
import random
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import session, redirect, url_for, render_template
import logging
import mariadb
app = Flask(__name__)
app.secret_key = 'baf9b68b0462ae76626618725c83460b'  # wag i delete

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'loleris1234',
    'database': 'attendance_tracker',
}

def get_db_connection():
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
       
        school_id = request.form['school_id']
        password = request.form['password']

        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user['password'], password):
           
            session['user_id'] = user['id']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'instructor':
                return redirect(url_for('instructor_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
           
            return render_template("login.html", error="Invalid login credentials")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        role = request.form['role']
        school_id = request.form['school_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email'] 

        
        if password != confirm_password:
            return "Passwords do not match", 400

        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return "Email is already registered. Please choose another one.", 400

        
        hashed_password = generate_password_hash(password)

        if role == 'Student':
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            name = f"{firstname} {lastname}"
        else:
            name = request.form['name']

        cursor.execute(
            "INSERT INTO users (name, password, role, school_id, email) VALUES (%s, %s, %s, %s, %s)",
            (name, hashed_password, role, school_id, email)
        )
        connection.commit()
        user_id = cursor.lastrowid

        image_dir = os.path.join('static', 'images')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        if role == 'Student':
            course = request.form['course']
            track = request.form['track']
            school_id_image_path = None

            if 'school_id_image' in request.files:
                school_id_image = request.files['school_id_image']
                filename = secure_filename(school_id_image.filename)
                school_id_image_path = os.path.join(image_dir, filename)
                school_id_image.save(school_id_image_path)

            cursor.execute(""" 
                INSERT INTO students (user_id, school_id, firstname, lastname, course, track, school_id_image) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, school_id, firstname, lastname, course, track, school_id_image_path))

        elif role == 'Instructor':
            instructor_id = request.form['instructor_id']
            subject = request.form['subject']
            cursor.execute(""" 
                INSERT INTO instructors (user_id, instructor_id, subject, school_id) 
                VALUES (%s, %s, %s, %s)
            """, (user_id, instructor_id, subject, school_id))

        elif role == 'Admin':
            cursor.execute("INSERT INTO admins (user_id, school_id) VALUES (%s, %s)", (user_id, school_id))

        connection.commit()
        connection.close()
        return redirect(url_for('login'))

    return render_template("signup.html")



@app.route("/update_profile", methods=["GET", "POST"])
def update_profile():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

       
        cursor.execute("SELECT * FROM users WHERE email = %s AND id != %s", (email, user_id))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Email is already registered. Please choose another one.", "error")
            return redirect(url_for('dashboard'))

        
        if password and confirm_password:
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return redirect(url_for('dashboard'))
            
            hashed_password = generate_password_hash(password)
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_password, user_id))
        elif not password and not confirm_password:
            
            generated_password = generate_random_password()
            hashed_password = generate_password_hash(generated_password)
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_password, user_id))
            flash(f"Your new password is: {generated_password}", "info")  # You may want to securely notify the user

       
        school_id_image_path = None
        if 'school_id_image' in request.files:
            school_id_image = request.files['school_id_image']
            if school_id_image.filename:
                image_dir = os.path.join('static', 'images')
                os.makedirs(image_dir, exist_ok=True)
                filename = secure_filename(school_id_image.filename)
                school_id_image_path = os.path.join(image_dir, filename)
                school_id_image.save(school_id_image_path)

       
        if school_id_image_path:
            cursor.execute("""
                UPDATE students
                SET firstname=%s, lastname=%s, school_id_image=%s
                WHERE user_id=%s
            """, (firstname, lastname, school_id_image_path, user_id))
        else:
            cursor.execute("""
                UPDATE students
                SET firstname=%s, lastname=%s
                WHERE user_id=%s
            """, (firstname, lastname, user_id))

        
        full_name = f"{firstname} {lastname}"
        cursor.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (full_name, email, user_id))

        connection.commit()
        connection.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('dashboard'))
    
    
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))



@app.route("/delete_user", methods=["POST"])
def delete_user():
    school_id = request.form.get('school_id')
    if not school_id:
        flash('School ID is required to delete the user', 'error')
        return redirect(url_for('admin_dashboard'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
    user = cursor.fetchone()

    if user:
        if user['role'] == 'student':
            cursor.execute("DELETE FROM students WHERE school_id = %s", (school_id,))
        elif user['role'] == 'instructor':
            cursor.execute("DELETE FROM instructors WHERE school_id = %s", (school_id,))
        elif user['role'] == 'admin':
            cursor.execute("DELETE FROM admins WHERE school_id = %s", (school_id,))
        cursor.execute("DELETE FROM users WHERE school_id = %s", (school_id,))
        connection.commit()
        flash('User deleted successfully', 'success')
    else:
        flash('User not found', 'error')

    connection.close()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        user_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        admin = cursor.fetchone()

        
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'instructor'")
        instructor_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()['count']

        cursor.execute(""" 
            SELECT i.instructor_id, u.name AS full_name, u.school_id AS email
            FROM instructors i
            JOIN users u ON i.user_id = u.id
        """)
        instructors = cursor.fetchall()

        cursor.execute(""" 
            SELECT s.school_id, CONCAT(s.firstname, ' ', s.lastname) AS full_name, u.school_id AS email
            FROM students s
            JOIN users u ON s.user_id = u.id
        """)
        students = cursor.fetchall()

        connection.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            instructors_html = render_template('instructors_list.html', instructors=instructors)
            students_html = render_template('student_list.html', students=students)
            return jsonify({
                'instructors_html': instructors_html,
                'students_html': students_html,
                'instructor_count': instructor_count,
                'student_count': student_count,
                'admin_count': admin_count
            })

        return render_template("admin_dashboard.html", 
                               admin_name=admin['name'],
                               instructors=instructors,
                               students=students,
                               instructor_count=instructor_count,
                               student_count=student_count,
                               admin_count=admin_count)
    else:
        return redirect(url_for('login'))


@app.route("/admin/add_instructor", methods=["POST"])
def add_instructor():
    instructor_name = request.form["instructor_name"]
    instructor_id = request.form["instructor_id"]
    instructor_subject = request.form["instructor_subject"]
    instructor_password = request.form["instructor_password"]
    school_id = request.form["school_id"]

    connection = get_db_connection()
    cursor = connection.cursor()
    hashed_password = generate_password_hash(instructor_password)
    cursor.execute(""" 
        INSERT INTO users (name, password, role, school_id) 
        VALUES (%s, %s, %s, %s)
    """, (instructor_name, hashed_password, "instructor", instructor_id))
    user_id = cursor.lastrowid
    cursor.execute(""" 
        INSERT INTO instructors (user_id, instructor_id, subject, school_id)
        VALUES (%s, %s, %s, %s)
    """, (user_id, instructor_id, instructor_subject, school_id))
    connection.commit()
    connection.close()
    flash("Instructor added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/instructor_dashboard")
def instructor_dashboard():
    if 'role' in session and session['role'] == 'instructor':
        user_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT u.name, u.school_id, i.instructor_id, i.subject 
            FROM users u
            JOIN instructors i ON u.id = i.user_id
            WHERE u.id = %s
        """, (user_id,))
        instructor = cursor.fetchone()
        connection.close()
        return render_template("instructor_dashboard.html", instructor=instructor)
    else:
        return redirect(url_for('login'))
    
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
        
        ("Computer Programming 1 | IT 101 | 6:00PM - 6:05PM", 18, 18.0833),
        ("Computer Programming 1 | IT 101 | 9:00PM - 10:00PM", 21, 22),
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

        if student:
           
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
                    ("Computer Programming 1 | IT 101 | 6:00PM - 6:05PM", 18, 18.0833),
                    ("Computer Programming 1 | IT 101 | 9:00PM - 10:00PM", 21, 22),
                    ("Free Time | N/A | 6:18PM - 6:25PM", 18.3, 18.4167),
                ],
                "Sunday": [
                    ("Contemporary World | GEC 6 | 9:00AM - 11:30AM", 9, 11.5),
                    ("Introduction to Computing | IT 100 | 1:00PM - 3:00PM", 13, 15),
                ]
            }

            
            timezone = pytz.timezone("Asia/Manila")
            now = datetime.now(timezone)
            current_day = now.strftime("%A")
            current_hour = now.hour + now.minute / 60

            
            logging.info(f"Current Time: {now}, Current Day: {current_day}, Current Hour: {current_hour}")

            
            cursor.execute("""
                SELECT subject_name FROM attendance WHERE student_id = %s AND DATE(date) = %s
            """, (user_id, now.date()))
            marked_subjects = [row['subject_name'] for row in cursor.fetchall()]

            
            logging.info(f"Marked subjects for today: {marked_subjects}")

            active_subjects = []
            today_schedule = subject_schedule.get(current_day, [])

            for subject in today_schedule:
                subject_name, start_time, end_time = subject

               
                logging.info(f"Checking subject: {subject_name} - Start Time: {start_time}, End Time: {end_time}")

                
                if start_time <= current_hour <= end_time:
                    status = 'on_time'
                elif current_hour > end_time:
                    status = 'late'
                else:
                    status = 'upcoming'

                attended_on_time = subject_name in marked_subjects

                
                cursor.execute("""
                    SELECT s.school_id 
                    FROM attendance a
                    JOIN students s ON a.student_id = s.user_id
                    WHERE a.subject_name = %s AND a.date = %s
                """, (subject_name, now.date()))
                student_list = cursor.fetchall()

                active_subjects.append({
                    'subject_name': subject_name,
                    'status': status,
                    'attended_on_time': attended_on_time,
                    'student_list': student_list 
                })

            
            connection.close()

            return render_template(
                "dashboard.html", 
                student_name=student['name'], 
                student_id=student['school_id'],
                user=student,
                active_subjects=active_subjects
            )
        else:
            connection.close()
            logging.error(f"Student with user_id {user_id} not found.")
            return "Student not found", 404
    else:
        logging.warning("Unauthorized access attempt, role is not student.")
        return redirect(url_for('login'))






@app.route('/logout', methods=["POST"])
def logout():
    session.clear()  
    return redirect(url_for('index'))  

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

logging.basicConfig(level=logging.INFO)
from datetime import datetime
import pytz

from flask import jsonify, request, session
from datetime import datetime
import pytz
import logging


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
   
    if 'user_id' not in session or session['role'] != 'student':
        logging.warning("Unauthorized access attempt.")
        return jsonify({
            "status": "error",
            "message": "Unauthorized access. Please log in again."
        }), 401

    
    subject = request.json.get('subject')
    if not subject:
        logging.warning("Subject is missing from the request payload.")
        return jsonify({
            "status": "error",
            "message": "Subject is required."
        })

    student_id = session['user_id']
    now = datetime.now(pytz.timezone('Asia/Manila'))
    date_today = now.strftime('%Y-%m-%d')
    time_now = now.strftime('%Y-%m-%d %H:%M:%S')  
    current_hour = now.hour + now.minute / 60  

    
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("Failed to connect to the database.")
            return jsonify({
                "status": "error",
                "message": "Database connection failed."
            })

        cursor = conn.cursor()

        logging.info(f"Checking if attendance for {subject} has already been marked today.")
        
        
        cursor.execute(""" 
            SELECT time_in, status FROM attendance
            WHERE student_id = %s AND subject_name = %s AND date = %s
        """, (student_id, subject, date_today))

        result = cursor.fetchone()
        
        if result:
            time_in = result[0]
            status = result[1]
            logging.info(f"Attendance already marked with status: {status}.")
            
            
            if current_hour > time_in.hour + time_in.minute / 60:
                if status != "late":
                    cursor.execute(""" 
                        UPDATE attendance
                        SET status = 'late'
                        WHERE student_id = %s AND subject_name = %s AND date = %s
                    """, (student_id, subject, date_today))
                    conn.commit()
                    logging.info("Updated attendance status to 'late'.")
                return jsonify({
                    "status": "success",
                    "message": f"Attendance already marked for {subject} today, but class has ended.",
                    "attendance_status": "late",  
                    "attendance_marked": True,  
                    "student_list": get_attendance_list(cursor, subject, date_today)  
                })
        
        
        logging.info(f"Inserting attendance: student_id={student_id}, subject={subject}, date={date_today}, time_in={time_now}")
        cursor.execute(""" 
            INSERT INTO attendance (student_id, subject_name, date, time_in)
            VALUES (%s, %s, %s, %s)
        """, (student_id, subject, date_today, time_now))
        conn.commit()

        
        cursor.execute(""" 
            SELECT * FROM attendance WHERE student_id = %s AND subject_name = %s AND date = %s
        """, (student_id, subject, date_today))
        result = cursor.fetchone()
        
        if result:
            logging.info(f"Attendance successfully inserted into database: {result}")
        else:
            logging.error(f"Failed to find inserted attendance for student_id={student_id}, subject={subject}")
        
        
        return jsonify({
            "status": "success",
            "message": f"Attendance marked for {subject}",
            "attendance_status": "on_time",  
            "attendance_marked": True,  
            "student_list": get_attendance_list(cursor, subject, date_today)  
        })

    except Exception as e:
        logging.error(f"Error marking attendance: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to mark attendance. Error: {str(e)}"
        })

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_attendance_list(cursor, subject, date_today):
    try:
        cursor.execute("""
            SELECT student_id, subject_name, time_in, status
            FROM attendance
            WHERE subject_name = %s AND date = %s
        """, (subject, date_today))
        attendance_list = cursor.fetchall()

        
        attendance_list = [
            {
                "student_id": row[0],
                "subject_name": row[1],
                "time_in": str(row[2]),  
                "status": row[3]
            }
            for row in attendance_list
        ]
        return attendance_list
    except Exception as e:
        logging.error(f"Error fetching attendance list: {str(e)}")
        return []  

@app.route('/get-time')
def get_time():
    timezone = pytz.timezone("Asia/Manila")
    now = datetime.now(timezone)
    formatted_time = now.strftime("%m/%d/%Y %I:%M:%S %p")
    return jsonify({'time': formatted_time})

if __name__ == '__main__':
    app.run(debug=True)
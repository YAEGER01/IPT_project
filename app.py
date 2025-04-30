import sched
from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time, timedelta
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
from flask import request, jsonify, session

from utils import row_to_dict, rows_to_dict

app = Flask(__name__)
app.secret_key = '77ddb26acf05b21b43c1f8cfda7062dc'  # wag i delete

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sulasok_tv',
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
                return redirect(url_for('student_dashboard'))
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

        # Fetch instructor info
        cursor.execute("""
            SELECT u.name, u.school_id, i.instructor_id
            FROM users u
            JOIN instructors i ON u.id = i.user_id
            WHERE u.id = %s
        """, (user_id,))
        instructor = cursor.fetchone()

        # Fetch active student count
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM subjects")
        subject_count = cursor.fetchone()['count']

        connection.close()

        return render_template("instructor_dashboard.html",
                               instructor=instructor,
                               student_count=student_count,
                               subject_count=subject_count)
    else:
        return redirect(url_for('login'))
    
@app.route("/subjects/add", methods=["POST"])
def add_subject():
    # Log request initiation 📝
    app.logger.info("🔄 Starting subject creation process...")
    
    # Authentication check 🔒
    if 'role' not in session or session['role'] != 'instructor':
        app.logger.warning("⚠️ Unauthorized access attempt - Missing role or invalid credentials")
        return jsonify({"error": "Unauthorized"}), 403
    
    # Parse incoming data 📨
    app.logger.debug("📦 Parsing JSON payload...")
    data = request.get_json()
    
    # Validate required fields ✅
    required_fields = ['code', 'name', 'day', 'start_time', 'end_time', 'course', 'track']
    missing = [f for f in required_fields if not data.get(f)]
    
    if missing:
        app.logger.error("❌ Missing required fields: {}".format(", ".join(missing)))
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    
    # Database operations 🗄️
    app.logger.debug("🔍 Connecting to database...")
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get instructor ID 👨‍🏫
        app.logger.debug("👥 Looking up instructor ID...")
        cursor.execute("SELECT instructor_id FROM instructors WHERE user_id = %s", (session['user_id'],))
        instructor = cursor.fetchone()
        
        if not instructor:
            app.logger.error("👋 Instructor not found for user_id: {}".format(session['user_id']))
            connection.close()
            return jsonify({"error": "Instructor not found"}), 404
        
        # Insert subject 📚
        app.logger.info("💾 Creating new subject...")
        cursor.execute("""
            INSERT INTO subjects (code, name, description, day, start_time, end_time, instructor_id, course, track)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['code'], data['name'], data.get('description'),
            data['day'], data['start_time'], data['end_time'],
            instructor['instructor_id'], data['course'], data['track']
        ))
        
# Convert string to time objects
        try:
            start_time_obj = datetime.strptime(data['start_time'], "%H:%M").time()
            end_time_obj = datetime.strptime(data['end_time'], "%H:%M").time()
        except ValueError:
            app.logger.error("❌ Invalid time format. Expected HH:MM.")
            return jsonify({"error": "Time must be in HH:MM format"}), 400

# Time constraints: 6:00 AM to 6:00 PM
        if not (time(6, 0) <= start_time_obj <= time(18, 0)):
            app.logger.warning("🚫 Start time out of bounds: {}".format(start_time_obj))
            return jsonify({"error": "Start time must be between 6:00 AM and 6:00 PM"}), 400

        if not (time(6, 0) <= end_time_obj <= time(18, 0)):
            app.logger.warning("🚫 End time out of bounds: {}".format(end_time_obj))
            return jsonify({"error": "End time must be between 6:00 AM and 6:00 PM"}), 400

# Make sure end is after start
        if end_time_obj <= start_time_obj:
            app.logger.warning("⏱️ End time must be after start time.")
            return jsonify({"error": "End time must be after start time"}), 400

        # Commit changes 💾
        app.logger.debug("💪 Committing changes to database...")
        connection.commit()
        
        # Success response 🎉
        app.logger.info("✅ Subject created successfully!")
        return jsonify({"message": "Subject added successfully!"})
        
    finally:
        # Cleanup 🧹
        app.logger.debug("🔩 Closing database connection...")
        connection.close()

@app.route("/subjects", methods=["GET"])
def get_subjects():
    if 'role' not in session or session['role'] != 'instructor':
        return jsonify({"error": "Unauthorized"}), 403

    user_id = session['user_id']

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT instructor_id FROM instructors WHERE user_id = %s", (user_id,))
    instructor = cursor.fetchone()

    if not instructor:
        connection.close()
        return jsonify({"error": "Instructor not found"}), 404

    instructor_id = instructor['instructor_id']  # ✅ now safe

    cursor.execute("""
        SELECT id, code, name, description, day, start_time, end_time, course, track
        FROM subjects
        WHERE instructor_id = %s
    """, (instructor_id,))

    subjects = cursor.fetchall()
    
     # 🔁 Convert time fields to string manually
    for subject in subjects:
        subject['start_time'] = str(subject['start_time'])
        subject['end_time'] = str(subject['end_time'])

    connection.close()
    return jsonify(subjects)


@app.route("/subjects/count", methods=["GET"])
def count_subjects():
    if 'role' not in session or session['role'] != 'instructor':
        return jsonify({"error": "Unauthorized"}), 403

    connection = get_db_connection()
    cursor = connection.cursor()

    # Count subjects (if you later want to count only THEIR subjects, you can filter by instructor_id if needed)
    cursor.execute("SELECT COUNT(*) AS count FROM subjects")
    result = cursor.fetchone()

    connection.close()

    return jsonify({"count": result['count']})

@app.route("/subjects/<int:subject_id>", methods=["GET"])
def get_subject(subject_id):
    # Log request initiation 📝
    app.logger.info("🔍 Fetching subject details...")
    
    try:
        # Database operations 🗄️
        app.logger.debug("🔄 Connecting to database...")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Query execution 🔍
        app.logger.debug("🔎 Executing SELECT query...")
        cursor.execute("""
            SELECT id, code, name, description, day, start_time, end_time, course, track
            FROM subjects WHERE id = %s
        """, (subject_id,))
        
        subject = cursor.fetchone()
        
        if not subject:
            app.logger.warning("⚠️ Subject not found: ID={}".format(subject_id))
            return jsonify({"error": "Subject not found"}), 404
        
        # Data processing 📊
        app.logger.debug("🔄 Processing time fields...")
        subject['start_time'] = str(subject['start_time'])
        subject['end_time'] = str(subject['end_time'])
        
        app.logger.info("✅ Subject fetched successfully!")
        return jsonify(subject)
        
    finally:
        # Cleanup 🧹
        app.logger.debug("🔩 Closing database connection...")
        connection.close()

@app.route("/subjects/<int:subject_id>", methods=["PUT"])
def update_subject(subject_id):
    if 'role' not in session or session['role'] != 'instructor':
        return jsonify({"error": "Unauthorized"}), 403

    connection = get_db_connection()
    cursor = connection.cursor()

    data = request.get_json()
    code = data.get('code')
    name = data.get('name')
    description = data.get('description')
    day = data.get('day')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    course = data.get('course')
    track = data.get('track')



    if not code or not name:
        connection.close()
        return jsonify({"error": "Code and Name are required"}), 400

    cursor.execute("""
    UPDATE subjects 
    SET code = %s, name = %s, description = %s, day = %s, start_time = %s, end_time = %s, course = %s, track = %s
    WHERE id = %s
    """, (code, name, description, day, start_time, end_time, course, track, subject_id))



    connection.commit()
    connection.close()

    return jsonify({"message": "Subject updated successfully!"})

@app.route("/subjects/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    if 'role' not in session or session['role'] != 'instructor':
        return jsonify({"error": "Unauthorized"}), 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
    connection.commit()
    connection.close()

    return jsonify({"message": "Subject deleted successfully."})

@app.route("/instructor/subjects")
def instructor_subjects():
    if 'user_id' not in session or session.get('role') != 'instructor':
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch instructor_id
    cursor.execute("SELECT instructor_id FROM instructors WHERE user_id = %s", (session['user_id'],))
    instructor = cursor.fetchone()

    if not instructor:
        connection.close()
        return "Instructor not found", 404

    # Fetch subjects
    cursor.execute("""
        SELECT id, code, name, course, track
        FROM subjects
        WHERE instructor_id = %s
    """, (instructor['instructor_id'],))

    subjects = cursor.fetchall()
    connection.close()

    return render_template("instructor_subjects.html", subjects=subjects)

@app.route("/instructor/attendance/<int:subject_id>")
def view_attendance(subject_id):
    if 'user_id' not in session or session.get('role') != 'instructor':
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch subject info
    cursor.execute("SELECT name, code FROM subjects WHERE id = %s", (subject_id,))
    subject = cursor.fetchone()

    if not subject:
        connection.close()
        return "Subject not found", 404

    # Fetch attendance for this subject
    cursor.execute("""
        SELECT students.firstname, students.lastname, attendance.date, attendance.time_in, attendance.status
        FROM attendance
        JOIN students ON attendance.student_id = students.user_id
        WHERE attendance.subject_name = %s
        ORDER BY attendance.date DESC, attendance.time_in DESC
    """, (subject['name'],))  # Assumes subject_name is used in attendance

    records = cursor.fetchall()
    connection.close()

    return render_template("instructor_attendance.html", subject=subject, records=records)


#Students
from flask import session, render_template, redirect
from datetime import datetime, timedelta
import pytz

@app.route("/student_dashboard")
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect("/login")

    user_id = session['user_id']
    print("➡️ Request received for /student_dashboard")
    print(f"👤 User ID from session: {user_id}")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("✅ Database connection established.")

        # Get student info
        cursor.execute("SELECT * FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            print("❌ Student not found.")
            connection.close()
            return "Student not found", 404

        name = f"{student['firstname']} {student['lastname']}"
        course = student['course']
        track = student['track']
        print(f"📚 Student data retrieved: {name} ({student['school_id']})")
        print(f"🎓 Course: {course}, Track: {track}")

        # Get today's date and time
        timezone = pytz.timezone("Asia/Manila")
        now = datetime.now(timezone)
        today = now.strftime('%A')
        print(f"📅 Today is {today} ({now.strftime('%H:%M:%S')})")

        # Get all subjects for student's course + track
        cursor.execute("""
            SELECT name AS subject_name, day, start_time, end_time
            FROM subjects
            WHERE course = %s AND track = %s
        """, (course, track))
        subjects = cursor.fetchall()

        today_subjects = []

        for subj in subjects:
            if subj['day'] != today or not subj['start_time'] or not subj['end_time']:
                continue

            start_time_raw = subj['start_time']

            if isinstance(start_time_raw, timedelta):
                start_time = (datetime.min + start_time_raw).time()
            else:
                start_time = start_time_raw

            subject_start = datetime.combine(now.date(), start_time)
            subject_start = timezone.localize(subject_start)

            open_window = subject_start - timedelta(minutes=5)
            close_window = subject_start + timedelta(minutes=5)
            is_active = open_window <= now <= close_window


            print(f"🧪 [{subj['subject_name']}] {subj['day']} {subj['start_time']}–{subj['end_time']} → "
                  f"{'🟢 ACTIVE' if is_active else '⚪ upcoming'}")

            today_subjects.append({
                'subject_name': subj['subject_name'],
                'day': subj['day'],
                'start_time': str(subj['start_time']),
                'end_time': str(subj['end_time']),
                'is_active': is_active
            })

        today_subjects.sort(key=lambda s: s['start_time'])
        print(f"📋 Showing {len(today_subjects)} subject(s) for today.")

        connection.close()
        print("🔒 Database connection closed.")
        print("✅ Rendering student dashboard.\n")

        return render_template("dashboard.html", user={'name': name}, subjects=today_subjects)


    except Exception as e:
        print(f"🔴 An error occurred: {e}")
        return "An error occurred while loading the dashboard.", 500

#history
@app.route("/student/attendance_history")
def attendance_history():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({"error": "Unauthorized"}), 403

    user_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT subject_name, DATE_FORMAT(time_in, '%%Y-%%m-%%d %%W %%h:%%i %%p') as time_in, status
        FROM attendance
        WHERE student_id = %s
        ORDER BY time_in DESC
    """, (user_id,))

    history = cursor.fetchall()
    connection.close()
    return jsonify(history)


#history

#End Students



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
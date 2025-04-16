from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash
import pymysql # type: ignore
from werkzeug.security import generate_password_hash
from datetime import datetime
import pytz
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

# Set a secret key to manage sessions securely
app.secret_key = 'baf9b68b0462ae76626618725c83460b'  # Replace with a secure key in production

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'loleris1234',  # Replace with your MariaDB password
    'database': 'attendance_tracker',
}

# Function to connect to the database
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
        try:
            school_id = request.form['school_id']
            password = request.form['password']
        except KeyError as e:
            return f"Missing field: {str(e)}", 400

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
        user = cursor.fetchone()
        connection.close()

        if user and user['password'] == password:
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

        if password != confirm_password:
            return "Passwords do not match", 400

        # Handle name based on role
        if role == 'Student':
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            name = f"{firstname} {lastname}"
        elif role == 'Instructor':
            name = request.form['name']
        elif role == 'Admin':
            name = request.form['name']
        else:
            return "Invalid role", 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert into users table
        cursor.execute(
            "INSERT INTO users (name, password, role, school_id) VALUES (%s, %s, %s, %s)",
            (name, password, role, school_id)
        )
        connection.commit()
        user_id = cursor.lastrowid

        # Check and create the static/images directory if it doesn't exist
        image_dir = os.path.join('static', 'images')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Role-specific table inserts
        if role == 'Student':
            course = request.form['course']
            track = request.form['track']
            school_id_image_path = None

            # Handle image upload
            if 'school_id_image' in request.files:
                school_id_image = request.files['school_id_image']
                
                # Secure the file name to prevent issues with special characters or spaces
                filename = secure_filename(school_id_image.filename)
                school_id_image_path = os.path.join(image_dir, filename)

                # Save the file to the directory
                school_id_image.save(school_id_image_path)

            # Insert student data into students table
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
            cursor.execute(""" 
                INSERT INTO admins (user_id, school_id) 
                VALUES (%s, %s)
            """, (user_id, school_id))

        connection.commit()
        connection.close()
        return redirect(url_for('login'))

    return render_template("signup.html")


@app.route("/delete_user", methods=["POST"])
def delete_user():
    if request.method == "POST":
        school_id = request.form.get('school_id')  # Use .get() to avoid KeyError

        if not school_id:
            flash('School ID is required to delete the user', 'error')
            return redirect(url_for('admin_dashboard'))

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
        user = cursor.fetchone()

        if user:
            # Delete related data from the specific tables
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
    else:
        return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        user_id = session['user_id']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get admin name
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        admin = cursor.fetchone()

        # Get counts for students, admins, and instructors
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'instructor'")
        instructor_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()['count']

        # Get instructors
        cursor.execute(""" 
            SELECT i.instructor_id, u.name AS full_name, u.school_id AS email
            FROM instructors i
            JOIN users u ON i.user_id = u.id
        """)
        instructors = cursor.fetchall()

        # Get students
        cursor.execute(""" 
            SELECT s.school_id, CONCAT(s.firstname, ' ', s.lastname) AS full_name, u.school_id AS email
            FROM students s
            JOIN users u ON s.user_id = u.id
        """)
        students = cursor.fetchall()

        connection.close()

        # Check if it's an AJAX request by inspecting the request headers
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

        # Normal page load
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
    if request.method == "POST":
        instructor_name = request.form["instructor_name"]
        instructor_id = request.form["instructor_id"]
        instructor_subject = request.form["instructor_subject"]
        instructor_password = request.form["instructor_password"]  # Plain text password
        school_id = request.form["school_id"]  # School ID

        # Insert into the users table (this is where the role is stored)
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert into the users table with role "instructor"
        hashed_password = generate_password_hash(instructor_password)
        cursor.execute(""" 
            INSERT INTO users (name, password, role, school_id) 
            VALUES (%s, %s, %s, %s)
        """, (instructor_name, hashed_password, "instructor", instructor_id))

        # Get the user_id of the newly inserted user (instructor)
        user_id = cursor.lastrowid

        # Insert into the instructors table with the user_id as a foreign key
        cursor.execute(""" 
            INSERT INTO instructors (user_id, instructor_id, subject, school_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, instructor_id, instructor_subject, school_id))  # Passing school_id here

        connection.commit()
        connection.close()

        # Flash a success message
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



@app.route("/dashboard")
def dashboard():
    if 'role' in session and session['role'] == 'student':
        user_id = session['user_id']

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Get student's name and school_id based on user_id
        cursor.execute("""
            SELECT name, school_id FROM users WHERE id = %s
        """, (user_id,))
        student = cursor.fetchone()
        connection.close()

        # Pass student's name and school_id to the template
        return render_template("dashboard.html", student_name=student['name'], student_id=student['school_id'])
    else:
        return redirect(url_for('login'))
    


#hakdog
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



@app.route('/get-time')
def get_time():
    tz = pytz.timezone('Asia/Manila')
    time = datetime.now(tz).strftime("%B %d, %Y %I:%M:%S %p")
    return jsonify({'time': time})

if __name__ == '__main__':
    app.run(debug=True)

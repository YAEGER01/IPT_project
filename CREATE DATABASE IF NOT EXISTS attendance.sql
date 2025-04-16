CREATE DATABASE IF NOT EXISTS attendance_tracker;

USE attendance_tracker;

-- Table for all users (students, instructors, admins)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'instructor', 'student') NOT NULL,
    school_id VARCHAR(20) UNIQUE,  -- School ID for login
    email VARCHAR(255) UNIQUE,     -- Optional, but can be used for admin or future needs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for students' specific details
CREATE TABLE IF NOT EXISTS students (
    user_id INT PRIMARY KEY,
    school_id VARCHAR(20) UNIQUE NOT NULL,  -- School ID as login identifier
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    course ENUM('BSIT', 'BSCS', 'BSECE', 'BSIS', 'BSPT') NOT NULL,
    track VARCHAR(50),
    school_id_image VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for instructors' specific details
CREATE TABLE IF NOT EXISTS instructors (
    user_id INT PRIMARY KEY,
    instructor_id VARCHAR(20) UNIQUE NOT NULL,
    subject VARCHAR(100) NOT NULL,
    school_id VARCHAR(20) UNIQUE NOT NULL,  -- School ID for login
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for admins' specific details (school_id for admin login)
CREATE TABLE IF NOT EXISTS admins (
    user_id INT PRIMARY KEY,
    school_id VARCHAR(20) UNIQUE NOT NULL,  -- Admin uses school_id for login
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
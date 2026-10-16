CREATE DATABASE IF NOT EXISTS placement_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE placement_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    cgpa DECIMAL(4, 2) NOT NULL,
    tenth_percentage DECIMAL(5, 2) NOT NULL,
    twelfth_percentage DECIMAL(5, 2) NOT NULL,
    branch VARCHAR(60) NOT NULL,
    backlogs INT NOT NULL DEFAULT 0,
    internship_experience ENUM('Yes', 'No') NOT NULL,
    technical_skill_level ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL,
    aptitude_score DECIMAL(5, 2) NOT NULL,
    communication_skills DECIMAL(4, 2) NOT NULL,
    projects_completed INT NOT NULL DEFAULT 0,
    placement_status ENUM('Placed', 'Not Placed') NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_students_branch (branch),
    INDEX idx_students_placement_status (placement_status)
);

CREATE TABLE IF NOT EXISTS prediction_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NULL,
    cgpa DECIMAL(4, 2) NOT NULL,
    tenth_percentage DECIMAL(5, 2) NOT NULL,
    twelfth_percentage DECIMAL(5, 2) NOT NULL,
    branch VARCHAR(60) NOT NULL,
    backlogs INT NOT NULL,
    internship_experience ENUM('Yes', 'No') NOT NULL,
    technical_skill_level ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL,
    aptitude_score DECIMAL(5, 2) NOT NULL,
    communication_skills DECIMAL(4, 2) NOT NULL,
    projects_completed INT NOT NULL,
    predicted_status ENUM('Placed', 'Not Placed') NOT NULL,
    placement_probability DECIMAL(6, 5) NULL,
    model_name VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_student
        FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE SET NULL,
    INDEX idx_prediction_created_at (created_at)
);

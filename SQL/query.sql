create database voting_system;
use voting_system;

INSERT INTO signup (user_name, gender, id_card, email, password, confirm_password, role) 
VALUES ('murtaza ahmad', 'male', '3730181884439', 'murtazaahmad2004@gmail.com', 'admin@2004', 'admin@2004', 'admin');

-- USERS (signup table)
CREATE TABLE signup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255),
    gender VARCHAR(10),
    id_card VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password TEXT,
    confirm_password TEXT,
    role VARCHAR(20) NOT NULL
);

-- CANDIDATES (linked to signup)
CREATE TABLE candidate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(255),
    gender VARCHAR(10),
    id_card VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    party_name VARCHAR(255),
    party_logo VARCHAR(255),
    profile_pic VARCHAR(255),
    CONSTRAINT fk_candidate_signup FOREIGN KEY (id_card) REFERENCES signup(id_card) ON DELETE CASCADE
);

-- LOGIN (Optional: but usually this can be merged with signup)
CREATE TABLE login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_card VARCHAR(25),
    password TEXT,
    CONSTRAINT fk_login_signup FOREIGN KEY (id_card) REFERENCES signup(id_card) ON DELETE CASCADE
);

-- VOTING REGISTRATION (linked to signup)
CREATE TABLE voting_registration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_card VARCHAR(25) UNIQUE,
    email VARCHAR(255) UNIQUE,
    CONSTRAINT fk_voting_registration_signup FOREIGN KEY (id_card) REFERENCES signup(id_card) ON DELETE CASCADE
);

-- VOTES (linked to candidates)
CREATE TABLE votes_full (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
    id_card VARCHAR(20), -- Candidate’s ID Card
    email VARCHAR(255) UNIQUE,
    party_name VARCHAR(255),
    party_logo VARCHAR(255),
    profile_pic VARCHAR(255),
    vote_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_votes_candidate FOREIGN KEY (id_card) REFERENCES candidate(id_card) ON DELETE CASCADE
);

-- ELECTIONS
CREATE TABLE elections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATETIME,
    end_date DATETIME,
    rules TEXT,
    is_active BOOLEAN DEFAULT FALSE
);

-- notifications --
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    user_role ENUM('admin','voter','candidate','all') DEFAULT 'all',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);
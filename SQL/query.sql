create database voting_system;
use voting_system;

CREATE TABLE signup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255),
    gender VARCHAR(10),
    id_card VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    password TEXT,
    confirm_password TEXT,
    role VARCHAR(20) NOT NULL
);

CREATE TABLE candidate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(255),
    gender VARCHAR(10),
    id_card VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    party_name VARCHAR(255),
    party_logo VARCHAR(255),
	profile_pic VARCHAR(255)
);

CREATE TABLE login (
id INT AUTO_INCREMENT PRIMARY KEY,
id_card varchar(25),
password TEXT
);

CREATE TABLE voting_registration (
id INT AUTO_INCREMENT PRIMARY KEY,
id_card varchar(25),
 email VARCHAR(255) UNIQUE
);

CREATE TABLE votes_full (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
	id_card VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    party_name VARCHAR(255),
    party_logo VARCHAR(255),
	profile_pic VARCHAR(255),
    vote_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
create database voting_system;
use voting_system;

CREATE TABLE signup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255),
    gender VARCHAR(10),
    id_card VARCHAR(20), -- safer than int
    email VARCHAR(255) UNIQUE,
    password TEXT
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
    party_name VARCHAR(255) NOT NULL,
    candidate_name VARCHAR(255) NOT NULL,
    picture VARCHAR(255) NOT NULL,
    party_symbol VARCHAR(255) NOT NULL,
    vote_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
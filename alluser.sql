CREATE DATABASE white_web;
USE white_web;

CREATE TABLE user (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(200)
);

SELECT * FROM user;

DROP TABLE user;
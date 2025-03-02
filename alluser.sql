CREATE DATABASE white_web;
USE white_web;

CREATE TABLE user (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(200)
);
INSERT INTO user VALUES ('user1', '1234');
INSERT INTO user VALUES ('user2', '4321');

SELECT * FROM user;

DROP TABLE user;
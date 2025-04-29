CREATE DATABASE white_web;
USE white_web;

CREATE TABLE user (
    username VARCHAR(20) NOT NULL,
    password VARCHAR(200) NOT NULL,
    phonenumber VARCHAR(11) NOT NULL,
    usertype INTEGER NOT NULL,
    PRIMARY KEY (username),
    UNIQUE (username)
);

CREATE TABLE orders (
    order_id INTEGER NOT NULL AUTO_INCREMENT,
    user1 VARCHAR(20),
    user2 VARCHAR(20),
    user3 VARCHAR(20),
    user4 VARCHAR(20),
    departure VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    earliest_departure_time TIME NOT NULL,
    latest_departure_time TIME NOT NULL,
    PRIMARY KEY (order_id)
);

SELECT * FROM user;

SELECT * FROM orders;

DROP TABLE user;
DROP TABLE orders;
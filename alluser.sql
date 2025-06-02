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
    driver VARCHAR(20),
    remark VARCHAR(100),
    PRIMARY KEY (order_id)
);

CREATE TABLE order_status (
    order_id INTEGER NOT NULL,
    status INTEGER DEFAULT 0, -- 0: 未开始, 1: 进行中, 2: 已完成
    user1_arrived BOOLEAN DEFAULT FALSE,
    user2_arrived BOOLEAN DEFAULT FALSE,
    user3_arrived BOOLEAN DEFAULT FALSE,
    user4_arrived BOOLEAN DEFAULT FALSE,
    driver_arrived BOOLEAN DEFAULT FALSE,
    completed_at DATETIME NULL,
    PRIMARY KEY (order_id),
    FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE TABLE driver_rating (
    rating_id INTEGER NOT NULL AUTO_INCREMENT,
    order_id INTEGER,
    driver_username VARCHAR(20),
    user_username VARCHAR(20),
    rating FLOAT NOT NULL, -- 1-5分
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (rating_id),
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (driver_username) REFERENCES user (username),
    FOREIGN KEY (user_username) REFERENCES user (username)
);

CREATE TABLE driver_average_rating (
    driver_username VARCHAR(20) NOT NULL,
    average_rating FLOAT DEFAULT 5.0,
    rating_count INTEGER DEFAULT 0,
    PRIMARY KEY (driver_username),
    FOREIGN KEY (driver_username) REFERENCES user (username)
);

SELECT * FROM user;

SELECT * FROM orders;

DROP TABLE user;
DROP TABLE orders;
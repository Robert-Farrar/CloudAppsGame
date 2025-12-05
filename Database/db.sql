DROP DATABASE IF EXISTS cloudgame;
CREATE DATABASE cloudgame;

DROP USER IF EXISTS 'cloud'@'%';
CREATE USER 'cloud'@'%' IDENTIFIED BY 'ThisIsThePassword1!';

GRANT ALL ON cloudgame.* TO 'cloud'@'%'

FLUSH PRIVILEGES;

USE cloudgame;

CREATE TABLE Card(
    cardID INT PRIMARY KEY AUTO_INCREMENT,
    cardValue INT,
    color VARCHAR(10),
    operation VARCHAR(15)
);

CREATE TABLE Player(
    playerID INT PRIMARY KEY AUTO_INCREMENT,
    ip CHAR(15) NOT NULL,
    points INT DEFAULT 0
);

CREATE TABLE Deck(
    deckID INT PRIMARY KEY AUTO_INCREMENT,
    playerID INT,
    cardID INT,
    FOREIGN KEY(playerID) REFERENCES Player(playerID) ON DELETE CASCADE,
    FOREIGN KEY(cardID) REFERENCES Card(cardID) ON DELETE CASCADE
);

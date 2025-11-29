DROP DATABASE IF EXISTS cloudgame;
DROP USER IF EXISTS 'cloud'@'localhost';
CREATE DATABASE cloudgame;
CREATE USER 'cloud'@'localhost' IDENTIFIED BY 'ThisIsThePassword1!';

-- uncomment when working with docker containers
-- DROP USER IF EXISTS 'cloud'@'%';
-- CREATE USER 'cloud'@'%' IDENTIFIED BY 'ThisIsThePassword1!';

-- GRANT ALL ON cloudgame.* TO 'cloud'@'%'


GRANT ALL ON cloudgame.* TO 'cloud'@'localhost';

FLUSH PRIVILEGES;

USE cloudgame;

CREATE TABLE Card(
    cardID INT PRIMARY KEY AUTO_INCREMENT,
    cardValue INT,
    color VARCHAR(10),
    operation VARCHAR(15)
);

<<<<<<< HEAD

create table Player(
    playerID int PRIMARY KEY AUTO_INCREMENT,
    ip char(15) NOT NULL,
    points int DEFAULT 0,
=======
CREATE TABLE Player(
    playerID INT PRIMARY KEY AUTO_INCREMENT,
    ip CHAR(15) NOT NULL,
    points INT DEFAULT 0
>>>>>>> main
);

CREATE TABLE Deck(
    deckID INT PRIMARY KEY AUTO_INCREMENT,
    playerID INT,
    cardID INT,
    FOREIGN KEY(playerID) REFERENCES Player(playerID) ON DELETE CASCADE,
    FOREIGN KEY(cardID) REFERENCES Card(cardID) ON DELETE CASCADE
);
<<<<<<< HEAD


create table Game(
    gameID int PRIMARY KEY AUTO_INCREMENT,
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    currentTurnPlayerID int,
    lastCardPlayedValue int,
    createAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(currentTurnPlayerID) REFERENCES Player(playerID)
);
=======
>>>>>>> main

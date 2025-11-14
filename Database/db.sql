drop database if exists cloudgame;
drop user if exists 'cloud'@'localhost';
create database cloudgame;
create user 'cloud'@'localhost' identified by 'ThisIsThePassword1!';

--uncomment when working with docker containers
-- drop user if exists 'cloud'@'Server';
-- create user 'cloud'@'server' identified by 'ThisIsThePassword1!;

--change to 'Server' for prod
grant all on cloud.* to 'cloud'@'localhost';

use cloudgame;

create table Card(
    cardID int PRIMARY KEY AUTO_INCREMENT,
    cardValue int,
    color varchar(10),
    operation varchar(15)
);


create table Player(
    playerID int PRIMARY KEY AUTO_INCREMENT,
    ip char(15) NOT NULL,
    points int DEFAULT 0,
);


create table Deck(
    deckID int PRIMARY KEY AUTO_INCREMENT,
    playerID int, 
    cardID int,
    FOREIGN KEY(playerID) REFERENCES Player(playerID) ON DELETE CASCADE, 
    FOREIGN KEY(cardID) REFERENCES Card(cardID) ON DELETE CASCADE
);


create table Game(
    gameID int PRIMARY KEY AUTO_INCREMENT,
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    currentTurnPlayerID int,
    lastCardPlayedValue int,
    createAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(currentTurnPlayerID) REFERENCES Player(playerID)
);
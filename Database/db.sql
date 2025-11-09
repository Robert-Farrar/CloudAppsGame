drop database if exists cloudgame;
drop user if exists 'cloud'@'localhost';
create user 'cloud'@'localhost' identified by 'ThisIsThePassword1!';

--uncomment when working with docker containers
-- drop user if exists 'cloud'@'Server';
-- create user 'cloud'@'server' identified by 'ThisIsThePassword1!;




create table Card(
    cardID int PRIMARY KEY AUTO_INCREMENT,
    cardValue int,
    color varchar(10),
    operation varchar(15)
);

create table Deck(
    deckID int PRIMARY KEY AUTO_INCREMENT,
    playerID int, 
    cardID int,
    FOREIGN KEY(playerID) REFERENCES Player(playerID) ON DELETE CASCADE, 
    FOREIGN KEY(cardID) REFERENCE Card(cardID) ON DELETE CASCADE
);


create table Player(
    playerID int PRIMARY KEY AUTO_INCREMENT,
    ip char(15) NOT NULL,
    points int DEFAULT 0,

);
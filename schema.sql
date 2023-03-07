DROP TABLE IF EXISTS Rooms;
CREATE TABLE Rooms (
    id INTEGER PRIMARY KEY autoincrement,
    title TEXT NOT NULL,
    floor_name TEXT NOT NULL,
    slug TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

DROP TABLE IF EXISTS Links;
CREATE TABLE Links (
    id INTEGER PRIMARY KEY autoincrement,
    url TEXT NOT NULL,
    domainName TEXT NOT NULL,
    description TEXT NOT NULL,
    label TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    FOREIGN KEY (room_id) REFERENCES Rooms(id)
);

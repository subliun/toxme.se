PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE records (
	user_id INTEGER NOT NULL, 
	name VARCHAR, 
	bio VARCHAR, 
	public_key VARCHAR, 
	checksum VARCHAR, 
	privacy INTEGER, 
	timestamp DATETIME, 
	sig VARCHAR, 
	pin VARCHAR, 
	password BLOB NOT NULL, 
	PRIMARY KEY (user_id), 
	UNIQUE (name), 
	UNIQUE (public_key)
);
COMMIT;

CREATE TABLE IF NOT EXISTS user(
  id         TEXT PRIMARY KEY,
  role       INTEGER,
  profile_id INTEGER
);

CREATE TABLE IF NOT EXISTS profile(
  id           INTEGER PRIMARY KEY,
  address_id   INTEGER,
  first_name   TEXT,
  last_name    TEXT,
  email        TEXT,
  iban         TEXT,
  phone_number TEXT
);

CREATE TABLE IF NOT EXISTS profile_address(
  id                   INTEGER PRIMARY KEY,
  current_postal_code  TEXT,
  current_house_number TEXT,
  current_address      TEXT
);

CREATE TABLE IF NOT EXISTS loan_request(
  id            INTEGER,
  user_id       TEXT,
  house_id      INTEGER,
  mortgage_type INTEGER,
  bank_id       TEXT,
  description   TEXT,
  amount_wanted FLOAT,
  status        INTEGER,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS house(
  id                  INTEGER PRIMARY KEY,
  postal_code         TEXT,
  house_number        TEXT,
  address             TEXT,
  price               FLOAT,
  url                 TEXT,
  seller_phone_number TEXT,
  seller_email        TEXT
);

CREATE TABLE IF NOT EXISTS mortgage(
  id              INTEGER,
  user_id         TEXT,
  bank_id         TEXT,
  house_id        INTEGER,
  amount          FLOAT,
  bank_amount     FLOAT,
  mortgage_type   INTEGER,
  interest_rate   FLOAT,
  max_invest_rate FLOAT,
  default_rate    FLOAT,
  duration        INTEGER,
  risk            TEXT,
  status          INTEGER,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS campaign(
  id               INTEGER,
  user_id          TEXT,
  mortgage_id      INTEGER,
  mortgage_user_id TEXT,
  amount           FLOAT,
  end_time         INTEGER,
  completed        INTEGER,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS investment(
  id               INTEGER,
  user_id          TEXT,
  amount           FLOAT,
  duration         INTEGER,
  interest_rate    FLOAT,
  campaign_id      INTEGER,
  campaign_user_id TEXT,
  status           INTEGER,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS blockchain(
  id                          INTEGER PRIMARY KEY,
  benefactor                  TEXT NOT NULL,
  beneficiary                 TEXT NOT NULL,
  agreement_benefactor        TEXT,
  agreement_beneficiary       TEXT,
  sequence_number_benefactor  INTEGER NOT NULL,
  sequence_number_beneficiary INTEGER NOT NULL,
  previous_hash_benefactor    TEXT NOT NULL,
  previous_hash_beneficiary   TEXT NOT NULL,
  signature_benefactor        TEXT NOT NULL,
  signature_beneficiary       TEXT NOT NULL,
  insert_time                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  hash_block                  TEXT NOT NULL,
  previous_hash               TEXT NOT NULL,
  sequence_number             INTEGER NOT NULL
);

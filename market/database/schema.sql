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
  id                   INTEGER,
  user_id              TEXT,
  bank_id              TEXT,
  house_id             INTEGER,
  amount               FLOAT,
  bank_amount          FLOAT,
  mortgage_type        INTEGER,
  interest_rate        FLOAT,
  max_invest_rate      FLOAT,
  default_rate         FLOAT,
  duration             INTEGER,
  risk                 TEXT,
  status               INTEGER,
  loan_request_id      INTEGER,
  loan_request_user_id TEXT,
  contract_id          TEXT,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS campaign(
  id               INTEGER,
  user_id          TEXT,
  mortgage_id      INTEGER,
  mortgage_user_id TEXT,
  amount           FLOAT,
  amount_invested  FLOAT,
  end_time         INTEGER,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS investment(
  id               INTEGER,
  user_id          TEXT,
  owner_id         TEXT,
  amount           FLOAT,
  duration         INTEGER,
  interest_rate    FLOAT,
  campaign_id      INTEGER,
  campaign_user_id TEXT,
  status           INTEGER,
  contract_id      TEXT,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS transfer(
  id                       INTEGER,
  user_id                  TEXT,
  iban                     TEXT,
  amount                   FLOAT,
  investment_id            INTEGER,
  investment_user_id       TEXT,
  status                   INTEGER,
  contract_id              TEXT,
  confirmation_contract_id TEXT,
  PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS contract(
  id              TEXT PRIMARY KEY,
  previous_hash   TEXT,
  from_public_key TEXT NOT NULL,
  from_signature  TEXT,
  to_public_key   TEXT NOT NULL,
  to_signature    TEXT,
  document        TEXT NOT NULL,
  type            INTEGER NOT NULL,
  time            TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS block(
  id                TEXT PRIMARY KEY,
  previous_hash     TEXT NOT NULL,
  merkle_root_hash  TEXT NOT NULL,
  creator           TEXT NOT NULL,
  creator_signature TEXT NOT NULL,
  target_difficulty TEXT NOT NULL,
  time              TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS block_contract(
  block_id    TEXT NOT NULL,
  contract_id TEXT NOT NULL,
  position    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (block_id, contract_id)
);

CREATE TABLE IF NOT EXISTS block_index(
  block_id TEXT PRIMARY KEY,
  height   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS user(
  id         TEXT PRIMARY KEY,
  role       INT,
  profile_id INT
);

CREATE TABLE IF NOT EXISTS profile(
  id           INTEGER PRIMARY KEY,
  address_id   INT,
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
  id            TEXT PRIMARY KEY,
  user_id       TEXT,
  house_id      INT,
  mortgage_type INT,
  bank_id       TEXT,
  description   TEXT,
  amount_wanted FLOAT,
  status        INT
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
  id              TEXT PRIMARY KEY,
  user_id         TEXT,
  bank_id         TEXT,
  house_id        INT,
  amount          FLOAT,
  bank_amount     FLOAT,
  mortgage_type   INT,
  interest_rate   FLOAT,
  max_invest_rate FLOAT,
  default_rate    FLOAT,
  duration        INT,
  risk            TEXT,
  status          INT,
  campaign_id     TEXT
);

CREATE TABLE IF NOT EXISTS campaign(
  id          TEXT PRIMARY KEY,
  user_id     TEXT,
  mortgage_id INT,
  amount      FLOAT,
  end_time    INT,
  completed   INT
);

CREATE TABLE IF NOT EXISTS investment(
  id            TEXT PRIMARY KEY,
  user_id       TEXT,
  amount        FLOAT,
  duration      INT,
  interest_rate FLOAT,
  campaign_id   TEXT,
  status        INT
);

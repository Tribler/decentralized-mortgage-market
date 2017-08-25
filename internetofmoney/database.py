"""
This file contains everything related to persistence for Internet-of-Money.
"""
import os

import time

from dispersy.database import Database


class InternetOfMoneyDB(Database):
    """
    Persistence layer for the Internet-of-Money module.
    Connection layer to SQLiteDB.
    Ensures a proper DB schema on startup.
    """
    LATEST_DB_VERSION = 1

    def __init__(self, cache_dir):
        """
        Sets up the persistence layer ready for use.
        :param cache_dir: Path to the cache directory
        """
        db_path = os.path.join(cache_dir, os.path.join(u"iom.db"))
        super(InternetOfMoneyDB, self).__init__(db_path)
        self._logger.debug("Internet of Money database path: %s", db_path)
        self.open()

    def _getall(self, query, params):
        return self.execute(query, params).fetchall()

    def add_transaction(self, txid, from_iban, to_iban, amount, description):
        """
        Log a transaction by saving it to the database
        :param txid: The ID of the transaction
        :param from_iban: The source IBAN account number
        :param to_iban: The destination IBAN account number
        :param amount: The amount of money transferred
        :param description: The description of the transaction
        """
        self.execute(u"INSERT INTO transactions (timestamp, txid, from_iban, to_iban, amount, description) "
                     u"VALUES (?,?,?,?,?,?)", (int(round(time.time() * 1000)), unicode(txid), unicode(from_iban),
                                               unicode(to_iban), amount, unicode(description)))
        self.commit()

    def get_transactions(self, limit=100):
        """
        Return most recent transactions in the database.
        """
        return self._getall(u"SELECT timestamp, txid, from_iban, to_iban, amount, description FROM transactions "
                            u"ORDER BY timestamp DESC LIMIT ?", (limit,))

    def log_event(self, level, message):
        """
        Log an event by saving it to the database
        :param level: The logging level of this message
        :param message: The message to log
        """
        assert level in ['debug', 'info', 'warning', 'error']
        self.execute(
            u"INSERT INTO events (timestamp, level, message) VALUES(?,?,?)",
            (int(round(time.time() * 1000)), unicode(level), unicode(message)))
        self.commit()

    def get_events(self, limit=100):
        """
        Return most recent events in the database.
        """
        return self._getall(u"SELECT timestamp, level, message FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))

    def get_schema(self):
        """
        Return the schema for the database.
        """
        return u"""
        CREATE TABLE IF NOT EXISTS events(
         id                          INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
         timestamp                   LONG NOT NULL,
         level                       TEXT NOT NULL,
         message                     TEXT NOT NULL
         );

         CREATE TABLE IF NOT EXISTS transactions(
         timestamp                   LONG NOT NULL,
         txid                        TEXT NOT NULL,
         from_iban                   TEXT NOT NULL,
         to_iban                     TEXT NOT NULL,
         amount                      DOUBLE NOT NULL,
         description                 TEXT NOT NULL,

         PRIMARY KEY (txid)
         );

        CREATE TABLE option(key TEXT PRIMARY KEY, value BLOB);
        INSERT INTO option(key, value) VALUES('database_version', '%s');
        """ % str(self.LATEST_DB_VERSION)

    def get_upgrade_script(self, current_version):
        """
        Return the upgrade script for a specific version.
        :param current_version: the version of the script to return.
        """
        return None

    def open(self, initial_statements=True, prepare_visioning=True):
        return super(InternetOfMoneyDB, self).open(initial_statements, prepare_visioning)

    def close(self, commit=True):
        return super(InternetOfMoneyDB, self).close(commit)

    def check_database(self, database_version):
        """
        Ensure the proper schema is used by the database.
        :param database_version: Current version of the database.
        :return:
        """
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < self.LATEST_DB_VERSION:
            while database_version < self.LATEST_DB_VERSION:
                upgrade_script = self.get_upgrade_script(current_version=database_version)
                if upgrade_script:
                    self.executescript(upgrade_script)
                database_version += 1
            self.executescript(self.get_schema())
            self.commit()

        return self.LATEST_DB_VERSION

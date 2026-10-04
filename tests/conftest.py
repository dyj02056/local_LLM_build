import sqlite3

import pytest


@pytest.fixture
def sample_db(tmp_path):
    path = tmp_path / "shop.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE customer (id INTEGER PRIMARY KEY, name TEXT, city TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount INTEGER,
                             FOREIGN KEY (customer_id) REFERENCES customer(id));
        INSERT INTO customer VALUES (1, 'Kim', 'Seoul'), (2, 'Lee', 'Busan'), (3, 'Park', 'Seoul');
        INSERT INTO orders VALUES (1, 1, 100), (2, 1, 250), (3, 2, 80);
        """
    )
    conn.commit()
    conn.close()
    return path

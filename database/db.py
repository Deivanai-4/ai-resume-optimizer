"""
Database connection helper using mysql-connector-python.
Provides a get_db() function that returns a connection from the pool.
"""
import mysql.connector
from mysql.connector import pooling
from flask import current_app, g


def get_db():
    """Get a database connection from the app context."""
    if 'db' not in g:
        cfg = current_app.config
        try:
            g.db = mysql.connector.connect(
                host=cfg['DB_HOST'],
                port=cfg['DB_PORT'],
                user=cfg['DB_USER'],
                password=cfg['DB_PASSWORD'],
                database=cfg['DB_NAME'],
                charset='utf8mb4',
                autocommit=False
            )
        except mysql.connector.Error as err:
            current_app.logger.error(f"Database connection error: {err}")
            raise
    return g.db


def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def query_db(sql, args=(), one=False, commit=False):
    """Execute a query and return results."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, args)
        if commit:
            db.commit()
            return cursor.lastrowid
        rv = cursor.fetchall()
        return (rv[0] if rv else None) if one else rv
    except mysql.connector.Error as err:
        if commit:
            db.rollback()
        current_app.logger.error(f"Query error: {err} | SQL: {sql}")
        raise
    finally:
        cursor.close()


def execute_db(sql, args=(), get_id=False):
    """Execute a write query (INSERT/UPDATE/DELETE)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, args)
        db.commit()
        if get_id:
            return cursor.lastrowid
        return cursor.rowcount
    except mysql.connector.Error as err:
        db.rollback()
        current_app.logger.error(f"Execute error: {err} | SQL: {sql}")
        raise
    finally:
        cursor.close()


def init_app(app):
    """Register database teardown with the Flask app."""
    app.teardown_appcontext(close_db)

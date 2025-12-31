"""
Database utility functions for PostgreSQL operations.
Provides secure connection handling with environment variables and context managers.
"""
import os
import psycopg2
from psycopg2 import OperationalError, DatabaseError
import configparser
from contextlib import contextmanager
from typing import Optional, Dict


def load_db_config() -> Dict[str, str]:
    """
    Load database configuration from environment variables with fallback to config.ini.
    
    Environment variables take precedence:
    - DB_HOST
    - DB_PORT
    - DB_USER
    - DB_PASSWORD
    
    Returns:
        Dict[str, str]: Database configuration parameters
        
    Raises:
        ValueError: If configuration cannot be loaded from either source
    """
    # Try environment variables first
    if all(os.getenv(key) for key in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']):
        return {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
    
    # Fall back to config.ini
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        raise ValueError(
            "Database configuration not found. Please set environment variables "
            "(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD) or create config.ini file."
        )
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        db_config = config['postgres']
        return {
            'host': db_config['host'],
            'port': db_config['port'],
            'user': db_config['user'],
            'password': db_config['password']
        }
    except (KeyError, configparser.Error) as e:
        raise ValueError(f"Error reading config.ini: {e}")


@contextmanager
def get_db_connection(dbname: str = 'postgres', autocommit: bool = False):
    """
    Context manager for database connections.
    
    Args:
        dbname: Name of the database to connect to (default: 'postgres')
        autocommit: Whether to enable autocommit mode (default: False)
        
    Yields:
        psycopg2.connection: Database connection object
        
    Raises:
        OperationalError: If connection cannot be established
        DatabaseError: For other database-related errors
        
    Example:
        with get_db_connection('mydb') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM mytable")
            results = cur.fetchall()
    """
    conn = None
    try:
        config = load_db_config()
        conn = psycopg2.connect(
            dbname=dbname,
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port']
        )
        if autocommit:
            conn.autocommit = True
        yield conn
    except OperationalError as e:
        error_msg = f"Failed to connect to database '{dbname}': {str(e)}"
        raise OperationalError(error_msg) from e
    except DatabaseError as e:
        error_msg = f"Database error occurred: {str(e)}"
        raise DatabaseError(error_msg) from e
    finally:
        if conn is not None:
            conn.close()


def get_existing_databases() -> list:
    """
    Retrieve list of existing TGS databases.
    
    Returns:
        list: List of database names matching pattern 'tgsdb_%_%'
        
    Raises:
        OperationalError: If connection fails
        DatabaseError: If query execution fails
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(r"""
                    SELECT datname FROM pg_database
                    WHERE datname LIKE 'tgsdb\_%\_%' ESCAPE '\'
                    ORDER BY datname DESC;
                """)
                results = cur.fetchall()
                return [r[0] for r in results]
    except OperationalError as e:
        raise OperationalError(f"Failed to retrieve database list: {str(e)}") from e
    except DatabaseError as e:
        raise DatabaseError(f"Error querying databases: {str(e)}") from e


def database_exists(dbname: str) -> bool:
    """
    Check if a database exists.
    
    Args:
        dbname: Name of the database to check
        
    Returns:
        bool: True if database exists, False otherwise
        
    Raises:
        OperationalError: If connection fails
        DatabaseError: If query execution fails
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
                return cur.fetchone() is not None
    except (OperationalError, DatabaseError) as e:
        raise DatabaseError(f"Error checking if database exists: {str(e)}") from e


def terminate_database_connections(dbname: str) -> None:
    """
    Terminate all connections to a specific database.
    
    Args:
        dbname: Name of the database
        
    Raises:
        DatabaseError: If termination fails
    """
    try:
        with get_db_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid();
                """, (dbname,))
    except DatabaseError as e:
        raise DatabaseError(f"Error terminating connections to '{dbname}': {str(e)}") from e


def create_database_from_template(source_db: str, target_db: str, owner: Optional[str] = None) -> None:
    """
    Create a new database by cloning an existing one.
    
    Args:
        source_db: Name of the source database to clone
        target_db: Name of the new database to create
        owner: Database owner (defaults to current user from config)
        
    Raises:
        ValueError: If target database already exists
        DatabaseError: If database creation fails
    """
    # Check if target already exists
    if database_exists(target_db):
        raise ValueError(f"Database '{target_db}' already exists.")
    
    # Get owner from config if not specified
    if owner is None:
        config = load_db_config()
        owner = config['user']
    
    try:
        # Terminate connections to source database
        terminate_database_connections(source_db)
        
        # Create the new database
        with get_db_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                # Use quoted identifiers to handle special characters
                cur.execute(f"""
                    CREATE DATABASE "{target_db}"
                    WITH TEMPLATE "{source_db}"
                    OWNER {owner};
                """)
    except DatabaseError as e:
        raise DatabaseError(f"Failed to create database '{target_db}': {str(e)}") from e

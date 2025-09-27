import os, mysql.connector

def read_secret(secret_name):
    """Read secret value from mounted secret files."""
    try:
        with open(f"/etc/secrets/{secret_name}", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_db_connection():
    """Connect to MySQL using secrets."""
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "metacleaner-db"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=read_secret("DB_USER") or os.getenv("DB_USER", "REPLACE_USER"),
        password=read_secret("DB_PASSWORD") or os.getenv("DB_PASSWORD", "REPLACE_PASSWORD"),
        database=os.getenv("DB_NAME", "dbMetaCleaner")
    )
    return connection

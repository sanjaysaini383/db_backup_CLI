# Database Backup CLI Utility

A cross-database command-line tool for backing up and restoring databases with optional compression, logging, and cloud upload support.  
Currently supports MySQL, PostgreSQL, MongoDB, and SQLite.

---

## Features

- Supports multiple DBMS:
  - MySQL
  - PostgreSQL
  - MongoDB
  - SQLite
- Full database backup to a single file or directory (depending on DB type).
- Restore from generated backup files.
- Optional backup compression using `tar.gz`.
- Optional cloud upload:
  - AWS S3
  - (Extensible for GCS / Azure if you want to enable them later)
- Simple, JSON-based configuration.
- Operation logging to a log file.
- Extensible code structure:
  - Separate modules for CLI, DB operations, utilities.

---

## Project Structure

db-backup-cli/
├── cli.py # Main CLI entrypoint
├── db_operations.py # DB connection, backup & restore logic
├── utils.py # Logging, compression, cloud upload helpers, notifications
├── config.json # Local configuration (NOT committed)
├── config.example.json # Example configuration (safe to commit)
├── requirements.txt # Python dependencies
├── .gitignore # Ignored files (venv, backups, logs, config.json, etc.)
└── README.md # Project documentation


---

## Requirements

- Python 3.8+
- For MySQL:
  - MySQL server running locally or remotely
  - `mysql-connector-python`
- For PostgreSQL (optional):
  - PostgreSQL server
  - `psycopg2-binary`
- For MongoDB (optional):
  - MongoDB server
  - `pymongo`
- For cloud upload (optional):
  - AWS account and credentials (if using S3)

All required Python packages are listed in `requirements.txt`.

---

## Installation

### 1. Clone the repository
git clone https://github.com/<YOUR_USERNAME>/db-backup-cli.git
cd db-backup-cli


### 2. Create and activate a virtual environment

Create virtual environment
python -m venv venv

Activate (Windows)
venv\Scripts\activate

Activate (Linux/Mac)
source venv/bin/activate


### 3. Install dependencies
pip install -r requirements.txt



---

## Configuration

The tool uses a JSON configuration file to store database credentials and (optionally) cloud credentials.

### 1. Create `config.json`

Copy the example file and adapt it:


Edit `config.json` to match your environment. Minimal example for local MySQL:

{
"database": {
"host": "localhost",
"port": 3306,
"user": "backup_user",
"password": "backup123",
"database": "mydb"
}
}


If you want to enable S3 uploads:

{
"database": {
"host": "localhost",
"port": 3306,
"user": "backup_user",
"password": "backup123",
"database": "mydb"
},
"aws": {
"access_key": "YOUR_AWS_ACCESS_KEY",
"secret_key": "YOUR_AWS_SECRET_KEY",
"region": "us-east-1"
}
}


> `config.json` is intentionally excluded via `.gitignore` to avoid committing secrets.

---

## Usage

All commands are run from the project root with the virtual environment activated.

### General CLI format

python cli.py <operation> --db-type <db_type> --config config.json [options]


- `operation`:
  - `test`    – test database connection
  - `backup`  – create a backup
  - `restore` – restore from a backup file
- `db-type`:
  - `mysql`
  - `postgresql`
  - `mongodb`
  - `sqlite`

---

### 1. Test Database Connection

Use this first to confirm that credentials in `config.json` are correct.

python cli.py test --db-type mysql --config config.json



Expected output on success:

- Logs in `backup.log`
- Terminal message like:  
  `✓ Connected to mysql database`  
  `✓ Connection successful!`

---

### 2. Backup

#### Basic backup

python cli.py backup --db-type mysql --config config.json --output mydb_backup.sql


- For MySQL/PostgreSQL/SQLite:
  - Creates a `.sql` or `.dump` file depending on implementation.
- For MongoDB:
  - Creates a directory with BSON dumps.

#### Backup with compression

python cli.py backup --db-type mysql --config config.json
--output mydb_backup.sql --compress


- Creates `mydb_backup.sql.tar.gz`
- The original `mydb_backup.sql` file may be removed after compression (depending on implementation).

#### Backup with timestamped filename (Windows PowerShell)

python cli.py backup --db-type mysql --config config.json `
--output "mydb_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql" --compress


This will create files like:

- `mydb_20251211_111500.sql.tar.gz`

---

### 3. Restore

> Warning: Restore can overwrite existing data. Use on test databases first.

#### Restore from an uncompressed SQL file

python cli.py restore --db-type mysql --config config.json --backup-file mydb_backup.sql


The tool will:

1. Decompress the `tar.gz` file.
2. Restore the database from the decompressed SQL file.

---

## Logging

The tool logs all operations into a log file (default: `backup.log` in the project root).

- Each run logs:
  - Operation type (test/backup/restore)
  - Start/end timestamps
  - Database type and name
  - Success or failure messages
  - Errors/exceptions if any

You can specify a custom log file via `--log-file` (if your CLI supports it), or adjust the logger in `utils.py`.

---

## Implementation Overview

### `cli.py`

- Parses command-line arguments (operation, db-type, config path, output, compression, cloud options).
- Loads `config.json`.
- Initializes logging.
- Routes to the appropriate function in `db_operations.py` and `utils.py`:
  - `connect_to_db`
  - `backup_database`
  - `restore_database`
  - `compress_backup`
  - `decompress_backup`
  - `upload_to_cloud`
  - `send_slack_notification` (if you enable it)

### `db_operations.py`

Handles:

- Connecting to DB:
  - MySQL via `mysql.connector`
  - PostgreSQL via `psycopg2`
  - MongoDB via `pymongo`
  - SQLite via `sqlite3`
- Backups:
  - MySQL: Python-based export (CREATE TABLE + INSERT statements)
  - PostgreSQL: `pg_dump` (if you enable it)
  - MongoDB: `mongodump` (if you enable it)
  - SQLite: `iterdump()` to SQL file
- Restores:
  - MySQL: executes SQL from backup file
  - PostgreSQL: `pg_restore` (if enabled)
  - MongoDB: `mongorestore` (if enabled)
  - SQLite: executes SQL script

### `utils.py`

Provides helpers for:

- Logging setup (`setup_logging`)
- Compression:
  - `compress_backup()` – create `.tar.gz`
  - `decompress_backup()` – unpack archives
- Cloud uploads (optional):
  - `upload_to_cloud()` – S3 / GCS / Azure
- Notifications (optional):
  - `send_slack_notification()` – via webhook URL

---

## Extending the Project

Here are some ideas to extend the project further:

- Add incremental/differential backups per DB type.
- Add scheduling (cron on Linux, Task Scheduler on Windows) with a wrapper script.
- Add encryption for backup files before uploading to cloud.
- Add a `list-backups` command to show available backups in local or cloud storage.
- Add configuration validation with clear error messages.
- Build a small TUI (text UI) or a minimal web dashboard to trigger backups.

---

## Security Considerations

- Never commit `config.json` (contains credentials).
- Use least-privilege DB users (e.g., a dedicated `backup_user` with only the necessary permissions).
- Restrict access to your backup files and logs.
- If uploading to cloud, rotate your API keys and use IAM roles where possible.
- For production setups, consider encrypting backups at rest.

---

## Troubleshooting

### 1. `Access denied for user`

- Verify username/password in `config.json`.
- Check MySQL permissions:

GRANT ALL PRIVILEGES ON mydb.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;


### 2. `Unknown database 'mydb'`

- Confirm the database exists:

SHOW DATABASES;


- Update the `database` field in `config.json` accordingly.

### 3. `The system cannot find the file specified` (for `mysqldump`, `pg_dump`, etc.)

- Either install DB client tools and add them to PATH, or use the pure-Python backup implementation (as your current code does for MySQL).

---

## License

You can choose a license such as MIT. Example:

MIT License

Copyright (c) 2025 <Your Name>

Permission is hereby granted, free of charge, to any person obtaining a copy


---

## Author

- **Name:** Sanjay Kumar Saini  
- **GitHub:** [@sanjaysaini383](https://github.com/sanjaysaini383)


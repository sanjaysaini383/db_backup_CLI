# Database Backup CLI Utility

A cross-database command-line tool for backing up and restoring databases with optional compression, logging, and cloud upload support. Currently supports MySQL, PostgreSQL, MongoDB, and SQLite.

---

Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Logging](#logging)
- [Implementation overview](#implementation-overview)
- [Extending the project](#extending-the-project)
- [Security considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Author](#author)

---

## Features

- Multi-DBMS support: MySQL, PostgreSQL, MongoDB, SQLite
- Full backup and restore workflows
- Optional compression (tar.gz)
- Optional cloud upload (AWS S3; extensible to GCS/Azure)
- JSON-based configuration
- Operation logging
- Extensible modular code (CLI, DB ops, utils)

---

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/sanjaysaini383/db_backup_CLI.git
cd db_backup_CLI
```

2. Create and activate a virtual environment (Python 3.8+):

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy and edit the example config:

```bash
cp config.example.json config.json
# edit config.json to match your environment
```

---

## Requirements

- Python 3.8+
- Optional DB client libraries (listed in requirements.txt):
  - MySQL: `mysql-connector-python`
  - PostgreSQL: `psycopg2-binary`
  - MongoDB: `pymongo`
- For cloud uploads: AWS credentials if using S3

---

## Installation

Follow the Quick Start steps above to clone the repo, create a venv, and install dependencies.

---

## Configuration

Copy `config.example.json` -> `config.json` and fill in credentials. `config.json` is ignored via `.gitignore`.

Example minimal MySQL config:

```json
{
  "database": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "backup_user",
    "password": "backup123",
    "database": "mydb"
  }
}
```

Example with AWS S3:

```json
{
  "database": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "backup_user",
    "password": "backup123",
    "database": "mydb"
  },
  "aws": {
    "access_key": "YOUR_AWS_ACCESS_KEY",
    "secret_key": "YOUR_AWS_SECRET_KEY",
    "region": "us-east-1",
    "bucket": "your-backup-bucket"
  }
}
```

---

## Usage

Run commands from the project root with the virtual environment activated.

General CLI format:

```bash
python cli.py <operation> --db-type <db_type> --config config.json [options]
```

Operations:
- `test` — test database connection
- `backup` — create a backup
- `restore` — restore from a backup file

Supported db-type values: `mysql`, `postgresql`, `mongodb`, `sqlite`

Examples:

- Test connection:

```bash
python cli.py test --db-type mysql --config config.json
```

- Basic backup:

```bash
python cli.py backup --db-type mysql --config config.json --output mydb_backup.sql
```

- Backup with compression:

```bash
python cli.py backup --db-type mysql --config config.json --output mydb_backup.sql --compress
```

- Restore from file:

```bash
python cli.py restore --db-type mysql --config config.json --backup-file mydb_backup.sql
```

Notes:
- MySQL/Postgres/SQLite backups produce SQL/dump files; MongoDB creates a directory of BSON files.
- Compression yields a `.tar.gz` file (original SQL may be removed after compression depending on settings).

---

## Project structure

```
db-backup-cli/
├── cli.py               # Main CLI entrypoint
├── db_operations.py     # DB connection, backup & restore logic
├── utils.py             # Logging, compression, cloud upload helpers
├── config.json          # Local configuration (NOT committed)
├── config.example.json  # Example configuration (safe to commit)
├── requirements.txt     # Python dependencies
├── .gitignore           # Ignored files
└── README.md            # Project documentation
```

---

## Logging

- Default log file: `backup.log` in project root.
- Each run records operation type, timestamps, DB info, and errors.
- A custom log file can be specified via CLI (if supported) or by editing `utils.py` logger.

---

## Implementation overview

- cli.py: argument parsing, config loading, logging setup, routing to functions
- db_operations.py: connect, backup, restore for supported DBs (MySQL via mysql.connector, PostgreSQL via pg_dump/psycopg2, MongoDB via mongodump/pymongo, SQLite via sqlite3)
- utils.py: compression/decompression, upload_to_cloud, logging helpers, notifications

---

## Extending the project

Suggestions:
- Incremental/differential backups
- Scheduling (cron / Task Scheduler)
- Encrypt backups before upload
- `list-backups` command for local/cloud listings
- Configuration validation and clearer errors
- Simple TUI or web dashboard

---

## Security considerations

- Never commit `config.json` (contains credentials).
- Use least-privilege DB users.
- Restrict access to backup files and logs.
- When using cloud storage, rotate keys and prefer IAM roles.
- Consider encrypting backups at rest.

---

## Troubleshooting

Common issues and fixes:

- Access denied for user: verify credentials and MySQL permissions.

```sql
GRANT ALL PRIVILEGES ON mydb.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
```

- Unknown database: confirm the database exists (SHOW DATABASES;) and update `config.json`.
- Missing client tools (mysqldump/pg_dump): install DB client tools or use Python-based backup where available.

---

## License

Choose a license such as MIT. Example header:

```
MIT License

Copyright (c) 2025 Sanjay Kumar Saini

Permission is hereby granted, free of charge, to any person obtaining a copy
```

---

## Author

- Name: Sanjay Kumar Saini
- GitHub: @sanjaysaini383 (https://github.com/sanjaysaini383)

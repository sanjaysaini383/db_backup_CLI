import subprocess
import sqlite3
import mysql.connector
import psycopg2
import pymongo
import os


# ============= CONNECTION =============
def connect_to_db(db_type, config):
    """Connect to database and return connection object"""
    try:
        if db_type == "mysql":
            conn = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 3306),
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
        elif db_type == "postgresql":
            conn = psycopg2.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 5432),
                user=config['user'],
                password=config['password'],
                dbname=config['database']
            )
        elif db_type == "mongodb":
            conn = pymongo.MongoClient(
                f"mongodb://{config['user']}:{config['password']}@"
                f"{config.get('host', 'localhost')}:{config.get('port', 27017)}"
            )
        elif db_type == "sqlite":
            conn = sqlite3.connect(config['database'])
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        print(f"✓ Connected to {db_type} database")
        return conn
    
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


# ============= BACKUP =============
def backup_database(db_type, config, output_file, logger):
    """Perform database backup"""
    try:
        logger.info(f"Starting backup for {db_type}: {config['database']}")
        
        if db_type == "mysql":
            # Python-based backup (no mysqldump needed)
            conn = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 3306),
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
            
            cursor = conn.cursor()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"-- MySQL Backup\n")
                f.write(f"-- Database: {config['database']}\n\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    # Get CREATE TABLE statement
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    create_table = cursor.fetchone()[1]
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                    f.write(f"{create_table};\n\n")
                    
                    # Get all data
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        cursor.execute(f"DESCRIBE `{table_name}`")
                        columns = [col[0] for col in cursor.fetchall()]
                        column_names = ', '.join([f"`{col}`" for col in columns])
                        
                        # Insert data
                        for row in rows:
                            values = []
                            for v in row:
                                if v is None:
                                    values.append('NULL')
                                elif isinstance(v, (int, float)):
                                    values.append(str(v))
                                else:
                                    # Escape single quotes
                                    escaped = str(v).replace("'", "''")
                                    values.append(f"'{escaped}'")
                            
                            values_str = ', '.join(values)
                            f.write(f"INSERT INTO `{table_name}` ({column_names}) VALUES ({values_str});\n")
                        
                        f.write("\n")
                
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
            cursor.close()
            conn.close()
            logger.info(f"MySQL backup completed: {output_file}")
            return output_file
        
        elif db_type == "postgresql":
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            cmd = [
                "pg_dump",
                "-h", config.get('host', 'localhost'),
                "-p", str(config.get('port', 5432)),
                "-U", config['user'],
                "-F", "c",
                "-f", output_file,
                config['database']
            ]
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"PostgreSQL backup completed: {output_file}")
            return output_file
        
        elif db_type == "mongodb":
            cmd = [
                "mongodump",
                "--host", config.get('host', 'localhost'),
                "--port", str(config.get('port', 27017)),
                "--db", config['database'],
                "--out", output_file
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"MongoDB backup completed: {output_file}")
            return output_file
        
        elif db_type == "sqlite":
            conn = sqlite3.connect(config['database'])
            with open(output_file, 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            conn.close()
            logger.info(f"SQLite backup completed: {output_file}")
            return output_file
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


# ============= RESTORE =============
def restore_database(db_type, backup_file, config, logger):
    """Restore database from backup"""
    try:
        logger.info(f"Starting restore for {db_type} from: {backup_file}")
        
        if db_type == "mysql":
            conn = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 3306),
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
            
            cursor = conn.cursor()
            
            # Read and execute SQL file
            with open(backup_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Execute each statement
            for statement in sql_script.split(';\n'):
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"Warning executing statement: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"MySQL restore completed successfully")
            return True
        
        elif db_type == "postgresql":
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            cmd = [
                "pg_restore",
                "-h", config.get('host', 'localhost'),
                "-p", str(config.get('port', 5432)),
                "-U", config['user'],
                "-d", config['database'],
                backup_file
            ]
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"PostgreSQL restore completed successfully")
            return True
        
        elif db_type == "mongodb":
            cmd = [
                "mongorestore",
                "--host", config.get('host', 'localhost'),
                "--port", str(config.get('port', 27017)),
                "--db", config['database'],
                backup_file
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"MongoDB restore completed successfully")
            return True
        
        elif db_type == "sqlite":
            conn = sqlite3.connect(config['database'])
            with open(backup_file, 'r') as f:
                conn.executescript(f.read())
            conn.commit()
            conn.close()
            logger.info(f"SQLite restore completed successfully")
            return True
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False

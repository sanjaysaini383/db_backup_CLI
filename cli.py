import argparse
import json
import os
from utils import setup_logging, compress_backup, decompress_backup, upload_to_cloud, send_slack_notification
from db_operations import connect_to_db, backup_database, restore_database

def main():
    parser = argparse.ArgumentParser(description="Database Backup CLI Tool")
    
    # Core arguments
    parser.add_argument('operation', choices=['backup', 'restore', 'test'], 
                       help="Operation: backup, restore, or test connection")
    parser.add_argument('--db-type', required=True, choices=["mysql", "postgresql", "mongodb", "sqlite"])
    parser.add_argument('--config', required=True, help="Path to JSON config file")
    
    # Backup specific
    parser.add_argument('--output', help="Output backup file path")
    parser.add_argument('--compress', action='store_true', help="Compress the backup")
    
    # Restore specific
    parser.add_argument('--backup-file', help="Backup file to restore")
    
    # Cloud storage
    parser.add_argument('--cloud', choices=['s3', 'gcs', 'azure'], help="Cloud storage")
    parser.add_argument('--bucket', help="Cloud bucket name")
    
    # Logging
    parser.add_argument('--log-file', default='backup.log', help="Log file path")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_file)
    logger.info(f"Starting {args.operation} operation")
    
    # Load config
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
        db_config = config['database']
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        print(f"Error: {e}")
        return
    
    try:
        # Test connection
        if args.operation == 'test':
            conn = connect_to_db(args.db_type, db_config)
            if conn:
                print("✓ Connection successful!")
                logger.info(f"Connection test passed for {args.db_type}")
            else:
                print("✗ Connection failed!")
                logger.error("Connection test failed")
            return
        
        # Backup operation
        if args.operation == 'backup':
            if not args.output:
                args.output = f"backup_{args.db_type}_{db_config['database']}.sql"
            
            # Perform backup
            backup_file = backup_database(args.db_type, db_config, args.output, logger)
            
            if backup_file:
                print(f"✓ Backup created: {backup_file}")
                
                # Compress if requested
                if args.compress:
                    compressed_file = compress_backup(backup_file, backup_file + ".tar.gz", logger)
                    backup_file = compressed_file
                    print(f"✓ Backup compressed: {compressed_file}")
                
                # Upload to cloud if requested
                if args.cloud and args.bucket:
                    upload_to_cloud(args.cloud, backup_file, args.bucket, config, logger)
                    print(f"✓ Backup uploaded to {args.cloud}")
                
                # Send notification
                if config.get("slack_webhook"):
                    send_slack_notification(config["slack_webhook"], 
                                           f"Backup completed: {backup_file}", logger)
            else:
                print("✗ Backup failed!")
        
        # Restore operation
        elif args.operation == 'restore':
            if not args.backup_file:
                print("Error: --backup-file required for restore")
                return
            
            # Decompress if needed
            restore_file = decompress_backup(args.backup_file)
            
            # Perform restore
            if restore_database(args.db_type, restore_file, db_config, logger):
                print(f"✓ Database restored from: {args.backup_file}")
                
                # Send notification
                if config.get("slack_webhook"):
                    send_slack_notification(config["slack_webhook"], 
                                           f"Restore completed: {args.backup_file}", logger)
            else:
                print("✗ Restore failed!")
    
    except Exception as e:
        logger.error(f"Operation error: {e}")
        print(f"Error: {e}")
    
    logger.info(f"{args.operation} operation completed")

if __name__ == '__main__':
    main()

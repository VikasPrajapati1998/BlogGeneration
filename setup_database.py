"""
Setup script to create the MySQL database
Run this before starting the application
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DATABASE", "blog_db")
DB_PASSWORD = os.getenv("PASSWORD", "abcd%401234")

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server without specifying a database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to MySQL server")
        
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            for db in databases:
                print(f"   - {db['Database']}")
        
        connection.close()
        print(f"Database setup complete!")
        print(f"You can now run: python main.py")
        
    except pymysql.err.OperationalError as e:
        print(f"\Error connecting to MySQL: {e}")
        print("Troubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check if password in .env file is correct")
        print("3. Verify MySQL is installed and accessible")
        print("For Windows: Check MySQL service in Services")
        print("For Mac: brew services start mysql")
        print("For Linux: sudo systemctl start mysql")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("Blog Generation - Database Setup")
    print(f"Database Name: {DB_NAME}")
    print(f"Password: {'*' * len(DB_PASSWORD)}")
    print("="*60 + "\n")
    
    create_database()

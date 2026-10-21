import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

host = os.environ.get('DB_HOST', 'localhost')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
database = os.environ.get('DB_NAME', 'ai_career_platform')

print(f"Connecting to database '{database}' on {host}:{port} as '{user}'...")

try:
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()

    # 1. Create interview_sessions table if it doesn't exist
    print("Creating interview_sessions table if not exists...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        company_id INT NULL,
        resume_id INT NULL,
        session_metadata LONGTEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    print("interview_sessions table ready.")

    # 2. Check and add missing columns to interview_questions
    cursor.execute("DESCRIBE interview_questions;")
    existing_iq_cols = [row[0] for row in cursor.fetchall()]

    if 'options' not in existing_iq_cols:
        print("Adding 'options' column to interview_questions...")
        cursor.execute("ALTER TABLE interview_questions ADD COLUMN options TEXT NULL;")
        conn.commit()

    if 'correct_answer' not in existing_iq_cols:
        print("Adding 'correct_answer' column to interview_questions...")
        cursor.execute("ALTER TABLE interview_questions ADD COLUMN correct_answer VARCHAR(255) NULL;")
        conn.commit()

    if 'session_id' not in existing_iq_cols:
        print("Adding 'session_id' column to interview_questions...")
        cursor.execute("ALTER TABLE interview_questions ADD COLUMN session_id INT NULL;")
        conn.commit()
        print("Added session_id column.")

    # Try adding foreign key separately
    try:
        cursor.execute("""
        ALTER TABLE interview_questions
        ADD CONSTRAINT fk_iq_session FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE SET NULL;
        """)
        conn.commit()
        print("Added foreign key on session_id.")
    except Exception as e:
        print(f"Foreign key notice (may already exist or not supported): {e}")

    # Ensure category column can accept various categories like 'Logical Reasoning', 'Personalized'
    try:
        cursor.execute("ALTER TABLE interview_questions MODIFY COLUMN category VARCHAR(50) DEFAULT 'Technical';")
        conn.commit()
        print("Updated interview_questions.category column to VARCHAR(50).")
    except Exception as e:
        print(f"Modifying category column notice: {e}")

    # 3. Check and add ai_profile to companies if missing
    try:
        cursor.execute("DESCRIBE companies;")
        existing_comp_cols = [row[0] for row in cursor.fetchall()]
        if 'ai_profile' not in existing_comp_cols:
            print("Adding 'ai_profile' column to companies...")
            cursor.execute("ALTER TABLE companies ADD COLUMN ai_profile LONGTEXT NULL;")
            conn.commit()
    except Exception as e:
        print(f"Company check notice: {e}")

    conn.commit()
    print("[SUCCESS] Schema updated successfully!")
except Exception as e:
    print(f"[ERROR] Error during schema update: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()


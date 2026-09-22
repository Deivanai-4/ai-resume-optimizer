import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='deivanai&27',
        database='ai_career_platform'
    )
    cursor = conn.cursor()

    try:
        cursor.execute("""
        ALTER TABLE interview_questions 
        ADD COLUMN options TEXT NULL,
        ADD COLUMN correct_answer VARCHAR(255) NULL;
        """)
    except Exception as e:
        print(f"Adding columns failed: {e}")

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
    
    # Also add session_id to interview_questions to group them
    try:
        cursor.execute("""
        ALTER TABLE interview_questions
        ADD COLUMN session_id INT NULL,
        ADD FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE SET NULL;
        """)
    except Exception as e:
        print(f"Adding session_id failed: {e}")

    conn.commit()
    print("Schema updated successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()

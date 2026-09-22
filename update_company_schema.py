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

    cursor.execute("""
    ALTER TABLE companies 
    ADD COLUMN ai_profile LONGTEXT NULL;
    """)
    conn.commit()
    print("Schema updated successfully: added ai_profile to companies")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()

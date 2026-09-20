import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="deivanai&27",
        database="ai_career"
    )

    print("Database Connected Successfully!")

    conn.close()

except Exception as e:
    print(e)
import sqlite3

try:
    # Connect to database
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()

    # Fetch all rows from a table
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    # Print results
    for row in rows:
        print(row)

except sqlite3.Error as e:
    print("Database error:", e)
finally:
    if conn:
        conn.close()

from app import create_app, db
import sqlite3

app = create_app()

with app.app_context():
    # Create the new column using raw SQL since we don't have migrations
    # Connect to the SQLite database directly
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(audio_file)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'progress_percent' not in columns:
        print("Adding progress_percent column to audio_file table...")
        cursor.execute("ALTER TABLE audio_file ADD COLUMN progress_percent INTEGER DEFAULT 0")
        conn.commit()
        print("Database updated successfully!")
    else:
        print("Column progress_percent already exists.")
    
    conn.close()

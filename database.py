import sqlite3
from datetime import datetime

DB_NAME = "workout_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Workouts Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            primary_joint TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''')
    
    # History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            workout_name TEXT NOT NULL,
            duration_sec INTEGER NOT NULL,
            reps_left INTEGER NOT NULL,
            reps_right INTEGER NOT NULL
        )
    ''')
    
    # Insert default workouts if they don't exist
    default_workouts = [
        # Day 1: Bodyweight Push + Legs
        ("Scapula push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("Diamond push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("Archer push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("Ring push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("One arm push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("Dip", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("L-sit", "core", "Day 1: Bodyweight Push + Legs"),
        ("Tuck planche", "shoulder", "Day 1: Bodyweight Push + Legs"),
        ("Wall hand stand push up", "elbow", "Day 1: Bodyweight Push + Legs"),
        ("Squats", "knee", "Day 1: Bodyweight Push + Legs"),
        ("Step up", "knee", "Day 1: Bodyweight Push + Legs"),
        ("Adv shrimp squat", "knee", "Day 1: Bodyweight Push + Legs"),
        ("Archer squat", "knee", "Day 1: Bodyweight Push + Legs"),
        ("Calf raises", "ankle", "Day 1: Bodyweight Push + Legs"),
        ("Horse stance", "knee", "Day 1: Bodyweight Push + Legs"),
        
        # Day 2: Bodyweight Pull + Core
        ("Scapula pull up", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("Pull up", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("One arm row", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("One arm face pull", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("One arm curls", "elbow", "Day 2: Bodyweight Pull + Core"),
        ("Tuck front lever row", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("Tuck front lever raise", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("Chin up", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("Hang", "shoulder", "Day 2: Bodyweight Pull + Core"),
        ("Side plank", "core", "Day 2: Bodyweight Pull + Core"),
        ("Hollow body hold leg open", "core", "Day 2: Bodyweight Pull + Core"),
        ("Knees ab wheel", "core", "Day 2: Bodyweight Pull + Core"),
        ("Dragon flag", "core", "Day 2: Bodyweight Pull + Core"),
        ("Knee-Crunch / Flutter-Kick / Bicycle-Crunch", "core", "Day 2: Bodyweight Pull + Core"),
        ("Leg Lifts", "hip", "Day 2: Bodyweight Pull + Core"),
        ("One arm plank", "core", "Day 2: Bodyweight Pull + Core"),
        
        # Day 4: Weighted Push + Legs
        ("Dumbbell Bench Press", "elbow", "Day 4: Weighted Push + Legs"),
        ("Incline Dumbbell Press", "elbow", "Day 4: Weighted Push + Legs"),
        ("Cable Crossover", "shoulder", "Day 4: Weighted Push + Legs"),
        ("Standing Dumbbell Overhead Press", "elbow", "Day 4: Weighted Push + Legs"),
        ("Cable Tricep Push-down", "elbow", "Day 4: Weighted Push + Legs"),
        ("Cable Shoulder Press", "elbow", "Day 4: Weighted Push + Legs"),
        ("Lateral Raise", "shoulder", "Day 4: Weighted Push + Legs"),
        ("Jumping Squat", "knee", "Day 4: Weighted Push + Legs"),
        
        # Day 5: Weighted Pull + Core
        ("Cable Lat Pulldown", "shoulder", "Day 5: Weighted Pull + Core"),
        ("Cable Row", "shoulder", "Day 5: Weighted Pull + Core"),
        ("Weighted Pull-Up", "shoulder", "Day 5: Weighted Pull + Core"),
        ("Seated Cable Face Pull", "shoulder", "Day 5: Weighted Pull + Core"),
        ("Cable Bicep Curl", "elbow", "Day 5: Weighted Pull + Core"),
        ("Cable Hammer Curl", "elbow", "Day 5: Weighted Pull + Core"),
        ("Kneeling Cable Crunch", "core", "Day 5: Weighted Pull + Core"),
        
        # Keep old ones just in case they were logged under these names
        ("Bicep Curl", "elbow", "Legacy"),
        ("Squat", "knee", "Legacy"),
        ("Push-up", "elbow", "Legacy")
    ]
    
    for w in default_workouts:
        c.execute("INSERT OR IGNORE INTO workouts (name, primary_joint, type) VALUES (?, ?, ?)", w)
        
    conn.commit()
    conn.close()

def get_categories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT type FROM workouts")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return categories

def get_workouts_by_category(category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, primary_joint FROM workouts WHERE type = ?", (category,))
    workouts = c.fetchall()
    conn.close()
    return workouts

def get_all_workouts():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, primary_joint FROM workouts")
    workouts = c.fetchall()
    conn.close()
    return workouts

def save_workout_session(name, duration, reps_left, reps_right):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO history (date, workout_name, duration_sec, reps_left, reps_right)
        VALUES (?, ?, ?, ?, ?)
    ''', (date_str, name, duration, reps_left, reps_right))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY date DESC")
    history = c.fetchall()
    conn.close()
    return history

def delete_history(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def add_workout(name, primary_joint, workout_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO workouts (name, primary_joint, type) VALUES (?, ?, ?)", (name, primary_joint, workout_type))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already exists
    finally:
        conn.close()

def delete_workout(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM workouts WHERE name = ?", (name,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

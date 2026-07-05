from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
import traceback

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    # timeout=10 helps prevent "database is locked" errors
    conn = sqlite3.connect("alumni.db", check_same_thread=False, timeout=10)
    cursor = conn.cursor()
    # This creates the table with the 'created_at' column
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        name TEXT,
        dept TEXT,
        query TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    return conn

db_conn = get_db()

@app.post("/query/add")
async def add_query(data: dict):
    try:
        cursor = db_conn.cursor()
        # Using .get() ensures the backend won't fail if a field is missed
        cursor.execute("""
            INSERT INTO queries (student_id, name, dept, query, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(data.get("student_id", "N/A")), 
            str(data.get("name", "Unknown")), 
            str(data.get("dept", "N/A")), 
            str(data.get("query", "")), 
            datetime.now().isoformat()
        ))
        db_conn.commit()
        print("✅ Success: Query saved to database.")
        return {"status": "success"}
    except Exception as e:
        print("❌ BACKEND ERROR DETECTED:")
        print(traceback.format_exc()) 
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queries/all")
async def get_queries(dept: str = ""):
    cursor = db_conn.cursor()
    if dept:
        cursor.execute("SELECT * FROM queries WHERE dept LIKE ? ORDER BY id DESC", (f"%{dept}%",))
    else:
        cursor.execute("SELECT * FROM queries ORDER BY id DESC")
    rows = cursor.fetchall()
    # Map 'sid' so the frontend can display the student number
    return [{"id": r[0], "sid": r[1], "name": r[2], "dept": r[3], "query": r[4]} for r in rows]

@app.get("/queries/count")
async def get_count():
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM queries")
    return {"total": cursor.fetchone()[0]}

@app.delete("/query/delete/{qid}")
async def delete_query(qid: int):
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM queries WHERE id=?", (qid,))
    db_conn.commit()
    return {"message": "Deleted"}

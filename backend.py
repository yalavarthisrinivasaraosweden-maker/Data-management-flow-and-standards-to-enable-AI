from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

app = FastAPI(title="Data Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "data.db"

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: str
    updated_at: str

# API Routes
@app.get("/api/items", response_model=List[Item])
def get_items(category: Optional[str] = None):
    """Get all items, optionally filtered by category"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if category:
        cursor.execute("SELECT * FROM items WHERE category = ? ORDER BY created_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [Item(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    ) for row in rows]

@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """Get a specific item by ID"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return Item(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@app.post("/api/items", response_model=Item)
def create_item(item: ItemCreate):
    """Create a new item"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO items (name, description, category)
        VALUES (?, ?, ?)
    """, (item.name, item.description, item.category))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return get_item(item_id) # type: ignore

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemUpdate):
    """Update an existing item"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get existing item
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update only provided fields
    updates = []
    values = []
    if item.name is not None:
        updates.append("name = ?")
        values.append(item.name)
    if item.description is not None:
        updates.append("description = ?")
        values.append(item.description)
    if item.category is not None:
        updates.append("category = ?")
        values.append(item.category)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(item_id)
        cursor.execute(f"UPDATE items SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return get_item(item_id)

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    """Delete an item"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

@app.get("/api/categories")
def get_categories():
    """Get all unique categories"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"categories": categories}

# Serve frontend
@app.get("/")
def read_root():
    return FileResponse("index.html")

# Mount static files if needed
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Data Management System

A full-stack web application for data storage, access, and management built with Python (FastAPI) and vanilla JavaScript.

## Features

- ✅ **CRUD Operations**: Create, Read, Update, and Delete items
- ✅ **Category Filtering**: Filter items by category
- ✅ **Modern UI**: Beautiful, responsive interface with smooth animations
- ✅ **RESTful API**: Clean API endpoints for all operations
- ✅ **SQLite Database**: Lightweight database with automatic initialization
- ✅ **Real-time Updates**: Instant UI updates after operations

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the backend server:
```bash
python backend.py
```

Or using uvicorn directly:
```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## API Endpoints

- `GET /api/items` - Get all items (optional query param: `category`)
- `GET /api/items/{id}` - Get a specific item
- `POST /api/items` - Create a new item
- `PUT /api/items/{id}` - Update an item
- `DELETE /api/items/{id}` - Delete an item
- `GET /api/categories` - Get all unique categories

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

1. **Add Items**: Click "Add New Item" button to create new entries
2. **Edit Items**: Click "Edit" on any item card to modify it
3. **Delete Items**: Click "Delete" on any item card to remove it
4. **Filter by Category**: Use the dropdown to filter items by category
5. **Refresh**: Click the refresh button to reload all items

## Project Structure

```
.
├── backend.py          # FastAPI backend server
├── index.html          # Frontend interface
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── data.db            # SQLite database (created automatically)
```

## Technologies Used

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite3
- **Server**: Uvicorn

## License

MIT

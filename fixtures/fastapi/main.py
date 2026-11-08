"""Sample FastAPI application fixture for UAA testing."""

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Sample Store API", version="1.0.0")

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    is_admin_only: Optional[bool] = False

def get_current_user():
    return {"user_id": 42, "role": "user"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/v1/items")
def list_items(skip: int = 0, limit: int = Query(10, le=100)):
    """List available items."""
    return [{"id": 1, "name": "Widget", "price": 9.99}]

@app.get("/api/v1/items/{item_id}")
def get_item(item_id: int):
    """Retrieve single item by ID."""
    if item_id == 404:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "name": "Widget", "price": 9.99}

@app.post("/api/v1/items", status_code=201)
def create_item(item: Item, user: dict = Depends(get_current_user)):
    """Create a new item."""
    return {"id": 100, "name": item.name, "price": item.price}

@app.delete("/api/v1/items/{item_id}", status_code=204)
def delete_item(item_id: int, user: dict = Depends(get_current_user)):
    """Delete an item."""
    return None


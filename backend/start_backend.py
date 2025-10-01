# backend/start_backend.py
import uvicorn
import multiprocessing
from app.main import app

if __name__ == "__main__":
    # For development
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
    
    # For production, use:
    # uvicorn.run(
    #     "app.main:app",
    #     host="0.0.0.0",
    #     port=8000,
    #     workers=multiprocessing.cpu_count()
    # )

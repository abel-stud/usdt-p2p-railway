"""
Flask wrapper for Railway deployment
This file allows the FastAPI app to run on Railway's Flask-based infrastructure
"""
import os
import uvicorn
from src.main import app

# Railway expects app.py with Flask-like structure
# We'll run FastAPI through uvicorn programmatically

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
else:
    # For Railway deployment
    import threading
    import time
    
    def run_server():
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
    
    # Start FastAPI in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    # Export the FastAPI app for Railway
    application = app


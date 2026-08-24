import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("Starting GDG On Campus AI Assistant & Admin Dashboard Server...")
    print("Local Web Interface: http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

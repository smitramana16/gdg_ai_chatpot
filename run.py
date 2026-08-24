import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    
    print("==========================================================")
    print("🚀 Starting GDG On Campus AI Assistant & Dashboard Server")
    print("📍 Local URL: http://127.0.0.1:8000")
    print("==========================================================")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

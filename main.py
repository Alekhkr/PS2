"""Signal Lab Main Runner.

Allows running directly via:
    python main.py
    uvicorn main:app --reload
"""

import uvicorn
from signal_lab.server import app

if __name__ == "__main__":
    uvicorn.run("signal_lab.server:app", host="127.0.0.1", port=8000, reload=True)

"""Signal Lab Root ASGI Entrypoint.

Allows running directly from workspace root via:
    uvicorn app:app --reload
    uvicorn app:main --reload
    python app.py
"""

import uvicorn
from signal_lab.server import app

# Export alias so both `uvicorn app:app` and `uvicorn app:main` work
main = app

if __name__ == "__main__":
    uvicorn.run("signal_lab.server:app", host="127.0.0.1", port=8000, reload=True)

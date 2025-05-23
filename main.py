import os
import uvicorn

# starting server..
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8283))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)

import os
import uvicorn

# starting server..
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8281))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

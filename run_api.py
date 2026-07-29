"""Start the FastAPI server from the project root."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=False)

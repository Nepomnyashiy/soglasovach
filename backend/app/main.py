from fastapi import FastAPI

app = FastAPI(
    title="Soglasovach API",
    description="API for the corporate workflow automation service.",
    version="0.1.0",
)


@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to Soglasovach API!"}


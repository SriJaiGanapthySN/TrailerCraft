import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.routes import router

app = FastAPI(title="TrailerCraft API")


@app.get("/")
def root():
    """Quick check that server is reachable."""
    return {"status": "ok", "message": "TrailerCraft API is running"}


@app.get("/health")
def health():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # Bind to all interfaces so port is accessible
        port=8000,
        reload=True,
    )

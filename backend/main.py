from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.invoice_routes import router as invoice_router

app = FastAPI(
    title="C11 – Invoice Intelligence",
    description="Invoice and receipt extraction with prompt experiments and review warnings.",
    version="3.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "C11 – Invoice Intelligence API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(invoice_router)

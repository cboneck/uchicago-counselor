from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db
from app.routes import chat, courses, careers

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(courses.router, prefix="/api", tags=["courses"])
app.include_router(careers.router, prefix="/api", tags=["careers"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": f"{settings.app_name} is running"}

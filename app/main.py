from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.database import engine, Base
import app.db.models 
from app.core.logging import logger

from app.api.routes import jobs, certificates

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

app.include_router(jobs.router)
app.include_router(certificates.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
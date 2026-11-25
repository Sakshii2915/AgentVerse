"""AgentVerse FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import init_db
from app.api.endpoints import router as api_router
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    logger.info("Initializing AgentVerse backend services...")
    init_db()
    logger.info(
        "AgentVerse backend initialized. Search Provider: '%s' | LLM Configured: %s",
        settings.effective_search_provider,
        settings.is_openai_configured
    )
    yield
    logger.info("Shutting down AgentVerse backend services...")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} – Multi-Agent Research & Intelligence System",
    description=(
        "Autonomous multi-agent research platform powered by LangGraph, FastAPI, and PostgreSQL. "
        "Coordinates Supervisor, Researcher, Analyst, Fact-Checker, Reviewer, and Report Generator agents."
    ),
    version=settings.VERSION,
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root path to API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=False
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import webhook, insults
from api.utils import lifespan
from shared.config.logger import setup_logger
from shared.config.settings import settings

logger = setup_logger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title="Forget Ex Bot API",
    version="1.0.0",
    debug=settings.app.debug
)

origins=[
    "http://127.0.0.1:80",
]

app.add_middleware(
    CORSMiddleware, # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(webhook.router)
app.include_router(insults.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "Forget Ex Bot API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

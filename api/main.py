from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import webhook, insults
from api.utils import has_access, lifespan
from shared.config import setup_logger
from shared.config import settings

logger = setup_logger(__name__)

app = FastAPI(
    lifespan=lifespan,
    title="Forget Ex Bot API",
    version="1.0.0",
    docs_url="/swagger",
    debug=settings.app.debug,
)

app.add_middleware(
    CORSMiddleware, # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(webhook.router)
app.include_router(insults.router, dependencies=[Depends(has_access)])


@app.get("/")
async def root():
    return {"status": "ok", "service": "Forget Ex Bot API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

# if settings.app.debug:
#     import pydevd_pycharm
#
#     pydevd_pycharm.settrace(
#         host="host.docker.internal",
#         port=5678,
#         stdoutToServer=True,
#         stderrToServer=True,
#         suspend=False,
#     )

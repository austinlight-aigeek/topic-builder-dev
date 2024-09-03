import logging_config  # noqa: I001, F401. Import initializes logging infrastructure.
import secret_config  # noqa: F401. Import initializes secret environment variables.

from os import getenv

import uvicorn
from apis.routes.base import api_router
from exception_handlers import add_exception_handlers
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(api_router)
add_exception_handlers(app)

if __name__ == "__main__":
    uvicorn.run(app, host=getenv("UVICORN_HOST", "127.0.0.1"), port=80)

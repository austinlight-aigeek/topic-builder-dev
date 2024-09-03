import inspect
import logging

from crypto.security import ForbiddenError, UnauthorizedError, UserNotFoundError
from fastapi import FastAPI, HTTPException, Request
from jose import ExpiredSignatureError, JWTError
from templates import html_templates

# ruff: noqa: ARG001. `exc` arguments in this module are needed for compatibility.


async def _unauthorized_handler(request: Request, exc: UnauthorizedError):
    if request.url.path.startswith("/api"):
        raise HTTPException(401, "Bearer token not found!")
    return html_templates.body_response(request, "login.html", "Login")


async def _usernotfound_handler(request: Request, exc: UserNotFoundError):
    if request.url.path.startswith("/api"):
        raise HTTPException(401, "User not found!")
    return html_templates.body_response(request, "login.html", "Login")


async def _forbidden_handler(request: Request, exc: ForbiddenError):
    if request.url.path.startswith("/api"):
        raise HTTPException(403, "Operation not allowed.")
    return html_templates.body_response(request, "login.html", "Login")


async def _expired_handler(request: Request, exc: ExpiredSignatureError):
    if request.url.path.startswith("/api"):
        raise HTTPException(401, "Token expired")
    response = html_templates.body_response(
        request,
        "login.html",
        "Login",
        {"error": "Session expired. Please log in again."},
        headers={"HX-Retarget": "body"},
    )
    response.delete_cookie("access_token")
    return response


async def _jwterror_handler(request: Request, exc: JWTError):
    if request.url.path.startswith("/api"):
        raise HTTPException(401, "Token invalid")
    response = html_templates.body_response(
        request,
        "login.html",
        "Login",
        {"error": "Problem validating your token. Please log in again."},
        headers={"HX-Retarget": "body"},
    )
    response.delete_cookie("access_token")
    return response


async def _internalservererror_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api"):
        raise
    if request.url.path == "/login":
        error = "Internal server error"
        return html_templates.body_response("login.html", {"request": request, "error": error})
    return html_templates.modal_response(request, "Error", "Internal Server Error")


# Register exception handlers defined in this module
#   with their annotated exception types
def add_exception_handlers(app: FastAPI):
    for f in globals().values():
        if inspect.isfunction(f) and f.__module__ == __name__ and f.__name__.endswith("_handler"):
            arg_spec = inspect.getfullargspec(f)
            exception_type = arg_spec.annotations[arg_spec.args[1]]
            app.add_exception_handler(exception_type, f)
            logging.info("Exception handler %s registered for type %s", f.__name__, exception_type)

from datetime import UTC, datetime

from apis.routes.backend.login import authenticate_user
from apis.routes.frontend import get_edit_view_rulesets
from apis.schemas.login import LoginRequest
from crypto.security import create_access_token
from database.exports import SessionDep
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from templates import html_templates

router = APIRouter()


@router.post("/login", response_class=HTMLResponse)
async def login_for_access_token(request: Request, db: SessionDep, form: LoginRequest):
    user = await authenticate_user(form.username, form.password, db)
    if not user:
        error = "Incorrect username or password"
        return html_templates.body_response(request, "login.html", "Login", {"error": error})

    user.last_login = datetime.now(UTC)
    access_token = create_access_token(data={"sub": user.username})

    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    response = html_templates.landingpage_response(request, user, edit_rulesets, view_rulesets)
    response.set_cookie(key="access_token", value=f"{access_token}", httponly=True)
    return response


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    msg = "Logged out successfully"
    response = html_templates.body_response(request, "login.html", "Login", {"request": request, "msg": msg})
    response.delete_cookie("access_token")

    return response

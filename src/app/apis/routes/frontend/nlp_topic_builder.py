from datetime import UTC, datetime
from uuid import UUID, uuid4

import numpy as np
from apis.routes.frontend import get_edit_view_rulesets
from apis.schemas.ruleset import RulesetCreate, RulesetEdit
from crypto.security import UserDep
from database.exports import Ruleset, SessionDep
from expr.nodes import Group
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sql.query import generate_postgresql_query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from templates import html_templates

MIN_RULESET_NAME_LENGTH = 8

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_root(request: Request, user: UserDep, db: SessionDep):
    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    return html_templates.landingpage_response(request, user, edit_rulesets, view_rulesets)


@router.get("/create", response_class=HTMLResponse)
async def get_create(request: Request, user: UserDep, db: SessionDep):
    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    return html_templates.landingpage_response(request, user, edit_rulesets, view_rulesets)


@router.post("/create", response_class=HTMLResponse)
async def post_create(request: Request, user: UserDep, db: SessionDep, ruleset_create: RulesetCreate):
    if len(ruleset_create.name) < MIN_RULESET_NAME_LENGTH or any(
        not (c.isupper() or c == "_") for c in ruleset_create.name
    ):
        return html_templates.modal_response(
            request,
            "Validation Error",
            "Topic names must be made of uppercase letters and underscores and be at least 8 characters long.",
        )

    ruleset = Ruleset(
        id=uuid4(),
        owner_id=user.id,
        name=ruleset_create.name,
        last_update=datetime.now(UTC),
        expression=ruleset_create.expression.model_dump(by_alias=True),
        schema_version="1.0",
        is_active=ruleset_create.is_active,
    )
    try:
        db.add(ruleset)
        await db.flush()
    except IntegrityError:
        return html_templates.modal_response(
            request, "Validation Error", f"A topic named '{ruleset_create.name}' already exists!"
        )

    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    return html_templates.editruleset_response(request, user, ruleset, user, edit_rulesets, view_rulesets)


@router.get("/edit/{id_}", response_class=HTMLResponse)
async def get_edit(request: Request, user: UserDep, db: SessionDep, id_: UUID):
    ruleset = await db.execute(select(Ruleset).filter(Ruleset.id == id_))
    ruleset = ruleset.scalars().first()
    owner = await ruleset.awaitable_attrs.user_

    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    if ruleset is None:
        return html_templates.createruleset_response(request, user, edit_rulesets, view_rulesets)
    if ruleset.owner_id != user.id:
        return html_templates.viewruleset_response(request, user, ruleset, owner, edit_rulesets, view_rulesets)
    return html_templates.editruleset_response(request, user, ruleset, owner, edit_rulesets, view_rulesets)


@router.put("/edit/{id_}", response_class=HTMLResponse)
async def put_edit(request: Request, user: UserDep, db: SessionDep, id_: UUID, ruleset_edit: RulesetEdit):
    if len(ruleset_edit.name) < MIN_RULESET_NAME_LENGTH or any(
        not (c.isupper() or c == "_") for c in ruleset_edit.name
    ):
        return html_templates.modal_response(
            request,
            "Validation Error",
            "Topic names must be made of uppercase letters and underscores and be at least 8 characters long.",
        )

    ruleset = await db.execute(select(Ruleset).filter(Ruleset.id == id_))
    ruleset = ruleset.scalars().first()
    owner = await ruleset.awaitable_attrs.user_

    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    if ruleset is None:
        return html_templates.createruleset_response(request, user, edit_rulesets, view_rulesets)
    if ruleset.owner_id != user.id:
        return html_templates.viewruleset_response(request, user, ruleset, owner, edit_rulesets, view_rulesets)

    try:
        ruleset.name = ruleset_edit.name
        ruleset.expression = ruleset_edit.expression.model_dump(by_alias=True)
        ruleset.is_active = ruleset_edit.is_active
        await db.flush()
    except IntegrityError:
        return html_templates.modal_response(
            request, "Validation Error", f"A topic named '{ruleset_edit.name}' already exists!"
        )

    return html_templates.editruleset_response(request, user, ruleset, owner, edit_rulesets, view_rulesets)


@router.get("/view/{id_}", response_class=HTMLResponse)
async def get_view(request: Request, user: UserDep, db: SessionDep, id_: UUID):
    ruleset = await db.execute(select(Ruleset).filter(Ruleset.id == id_))
    ruleset = ruleset.scalars().first()
    owner = await ruleset.awaitable_attrs.user_

    edit_rulesets, view_rulesets = await get_edit_view_rulesets(user, db)
    if ruleset is None:
        return html_templates.createruleset_response(request, user, edit_rulesets, view_rulesets)
    return html_templates.viewruleset_response(request, user, ruleset, owner, edit_rulesets, view_rulesets)


@router.post("/query", response_class=HTMLResponse)
async def post_query(request: Request, root: Group, db: SessionDep, user: UserDep):  # noqa: ARG001. Depends arg used for auth
    sql, params = await generate_postgresql_query(root)
    connection = await db.connection()
    result = await connection.exec_driver_sql(sql, params)
    records = [r._asdict() for r in result.all()]

    param_strs = []
    for param in params:
        if isinstance(param, np.ndarray):
            param_strs.append("(query embedding)")
        else:
            param_strs.append(str(param))

    return html_templates.template_response(
        request, "_queryresult.html", {"sql": sql, "params": param_strs, "records": records}
    )

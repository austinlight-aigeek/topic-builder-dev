from database.exports import AsyncSession, Ruleset, User
from sqlalchemy import select


# Get Rulesets to populate Edit/View dropdowns
# Rulesets the user owns are eligible for Edit, while others are eligible for View
async def get_edit_view_rulesets(
    user: User, db: AsyncSession
) -> tuple[list[Ruleset], list[Ruleset]]:
    rulesets = await db.execute(select(Ruleset).order_by(Ruleset.name))
    rulesets = rulesets.scalars().all()

    edit_rulesets = []
    view_rulesets = []
    for r in rulesets:
        edit_rulesets.append(r) if r.owner_id == user.id else view_rulesets.append(r)

    return edit_rulesets, view_rulesets

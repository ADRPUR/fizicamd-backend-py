import uuid
from datetime import datetime, timezone

from app.core.security import create_access_token
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


def create_user_with_role(db, role_code: str):
    role = db.query(Role).filter(Role.code == role_code).first()
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        email=f"{role_code.lower()}_{uuid.uuid4().hex}@example.com",
        password_hash="x",
        status="ACTIVE",
        is_email_verified=False,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    if role:
        db.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, assigned_at=now))
        db.commit()
    token = create_access_token(str(user.id), user.email, [role_code])
    return user, token


def test_public_resources_pagination(client, db_session):
    teacher, token = create_user_with_role(db_session, "TEACHER")
    headers = {"Authorization": f"Bearer {token}"}

    category_payload = {"label": "Test Category", "group": "Test Group"}
    cat = client.post("/api/teacher/resource-categories", json=category_payload, headers=headers)
    assert cat.status_code == 200
    category_code = cat.json()["code"]

    resource_payload = {
        "categoryCode": category_code,
        "title": "Test Resource",
        "summary": "Short summary",
        "tags": ["physics"],
        "blocks": [{"type": "TEXT", "text": "Content"}],
        "status": "PUBLISHED",
    }
    created = client.post("/api/teacher/resources", json=resource_payload, headers=headers)
    assert created.status_code == 200

    public_list = client.get("/api/public/resources", params={"limit": 5, "page": 1})
    assert public_list.status_code == 200
    data = public_list.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

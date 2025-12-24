import uuid
from datetime import datetime, timezone

from app.core.security import create_access_token
from app.models.group import Group
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


def test_admin_group_flow(client, db_session):
    admin, admin_token = create_user_with_role(db_session, "ADMIN")
    teacher, _ = create_user_with_role(db_session, "TEACHER")
    headers = {"Authorization": f"Bearer {admin_token}"}

    group_name = f"Group {uuid.uuid4().hex}"
    create = client.post("/api/admin/groups", json={"name": group_name}, headers=headers)
    assert create.status_code == 201

    group = db_session.query(Group).filter(Group.name == group_name).first()
    assert group is not None

    add_member = client.post(
        f"/api/admin/groups/{group.id}/members",
        json={"userId": str(teacher.id), "memberRole": "TEACHER"},
        headers=headers,
    )
    assert add_member.status_code == 204

    get_group = client.get(f"/api/admin/groups/{group.id}", headers=headers)
    assert get_group.status_code == 200
    data = get_group.json()
    assert data["name"] == group_name

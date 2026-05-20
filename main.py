from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import engine, Base, get_db
from models import User
from schemas import (
    UserRegister,
    UserLogin,
    Token,
    UserProfileResponse,
    AdminProfileResponse,
    ProfileUpdate,
)
from auth import hash_password, verify_password, create_access_token
from dependencies import get_current_user, require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Auth API", lifespan=lifespan)


@app.post("/auth/register", response_model=UserProfileResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="username already registered.",
        )

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    dummy_hash = "$2b$12$dummy.hash.to.prevent.timing.attack.XXXXXXXXXX"

    password_valid = verify_password(
        data.password, user.hashed_password if user else dummy_hash
    )

    if not user or not password_valid:
        # Intentionally vague — don't reveal whether email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token)


@app.get("/profile/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@app.patch("/profile/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = data.model_dump(exclude_unset=True)

    if "email" in updated:
        result = await db.execute(select(User).where(User.email == updated["email"]))
        if result.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already in use")

    if "username" in updated:
        result = await db.execute(
            select(User).where(User.username == updated["username"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="Username already taken"
            )

    for key, value in updated.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


# Admin Routers
@app.get("/admin/users", response_model=list[AdminProfileResponse])
async def list_all_admin_users(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    return result.scalars().all()


@app.get("/admin/users/{user_id}", response_model=AdminProfileResponse)
async def get_admin_by_id(
    user_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@app.get("/admin/users/{user_id}/promote", response_model=AdminProfileResponse)
async def promote_user(
    user_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return user

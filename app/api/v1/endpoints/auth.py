from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserResponse, TokenResponse
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(User).where(User.email == user_in.email))
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists.")

        hashed_pwd = get_password_hash(user_in.password)
        user = User(email=user_in.email, hashed_password=hashed_pwd)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Swagger UI passes email inside form_data.username
        res = await db.execute(select(User).where(User.email == form_data.username))
        user = res.scalars().first()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        return TokenResponse(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

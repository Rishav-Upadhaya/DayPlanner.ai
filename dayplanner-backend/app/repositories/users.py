from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


class UserAlreadyExistsError(Exception):
    pass


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_or_create_google_user(self, email: str, full_name: str, google_sub: str | None = None, avatar_url: str | None = None) -> User:
        user = self.get_by_email(email=email)
        if user:
            if full_name:
                user.full_name = full_name
            if google_sub:
                user.google_sub = google_sub
            if avatar_url is not None:
                user.avatar_url = avatar_url
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        user = User(email=email, full_name=full_name, google_sub=google_sub, avatar_url=avatar_url)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_local_user(self, email: str, full_name: str, password: str) -> User:
        existing = self.get_by_email(email=email)
        if existing:
            raise UserAlreadyExistsError('User already exists')

        user = User(email=email, full_name=full_name, password_hash=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_local_user(self, email: str, password: str) -> User | None:
        user = self.get_by_email(email=email)
        if not user or not user.password_hash:
            return None
        if not verify_password(password=password, password_hash=user.password_hash):
            return None
        return user

    def get_or_create_by_id(self, user_id: str) -> User:
        user = self.get_by_id(user_id=user_id)
        if user:
            return user

        email = f'{user_id}@local.dayplanner.ai'
        user = User(id=user_id, email=email, full_name='DayPlanner Local User')
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

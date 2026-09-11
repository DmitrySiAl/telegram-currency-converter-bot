import os
from sqlalchemy import BigInteger, String, ForeignKey, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DB_URL = "sqlite+aiosqlite:///bot_database.db"

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language_code: Mapped[str] = mapped_column(String(2), default="en")
    favorites: Mapped[list["FavoriteCurrency"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class FavoriteCurrency(Base):
    __tablename__ = "favorite_currencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", on_delete="CASCADE"))
    currency_code: Mapped[str] = mapped_column(String(3))

    user: Mapped["User"] = relationship(back_populates="favorites")




async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user_language(user_id: int, telegram_lang: str = "en") -> str:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            bot_supported_languages = ["ru", "en", "de"]
            final_lang = telegram_lang if telegram_lang in bot_supported_languages else "en"

            user = User(user_id=user_id, language_code=final_lang)
            session.add(user)
            await session.commit()
            return final_lang

        return user.language_code


async def set_user_language(user_id: int, lang: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, language_code=lang)
            session.add(user)
        else:
            user.language_code = lang
        await session.commit()


async def get_user_favorites(user_id: int) -> list[str]:
    async with async_session() as session:
        result = await session.execute(
            select(FavoriteCurrency.currency_code).where(FavoriteCurrency.user_id == user_id)
        )
        return [row for row in result.scalars()]


async def toggle_favorite(user_id: int, currency: str) -> bool:
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.user_id == user_id))
        if not user_res.scalar_one_or_none():
            session.add(User(user_id=user_id))
            await session.flush()

        stmt = select(FavoriteCurrency).where(
            FavoriteCurrency.user_id == user_id,
            FavoriteCurrency.currency_code == currency
        )
        result = await session.execute(stmt)
        fav = result.scalar_one_or_none()

        if fav:
            await session.delete(fav)
            await session.commit()
            return False
        else:
            new_fav = FavoriteCurrency(user_id=user_id, currency_code=currency)
            session.add(new_fav)
            await session.commit()
            return True
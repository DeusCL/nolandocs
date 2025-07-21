from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean

from .base import BaseModel


class File(BaseModel):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[int] = mapped_column(String(255), nullable=False)

    document_metadata = relationship("DocumentMetadata", back_populates="file", cascade="all, delete-orphan")

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mlmodel import MLModelDB


class MLModelSettingsDB(Base, BaseMixin):
    repr_cols = ("model_id", "parameter", "parameter_value")

    model_id: Mapped[int] = mapped_column(
        ForeignKey("mlmodeldb.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID связанной модели",
    )

    parameter: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Название параметра"
    )
    parameter_value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Значение параметра в строковом формате"
    )

    # Связи
    mlmodel: Mapped["MLModelDB"] = relationship(
        back_populates="settings", lazy="joined"
    )

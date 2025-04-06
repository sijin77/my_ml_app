from datetime import datetime
from pydantic import BaseModel, ConfigDict
from db.models.user_roles import Roles


class UserRoleBase(BaseModel):
    role: Roles
    is_active: bool = True


# DTO для создания
class UserRoleCreate(UserRoleBase):
    user_id: int


# DTO для обновления
class UserRoleUpdate(BaseModel):
    role: Roles | None = None
    is_active: bool | None = None


# DTO для чтения (возврата из API)
class UserRoleRead(UserRoleBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

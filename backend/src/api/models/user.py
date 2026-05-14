from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from api.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

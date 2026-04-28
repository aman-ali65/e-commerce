from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class UserRole(Enum):
    CUSTOMER = "Customer"
    ADMIN = "Admin"
    SELLER = "Seller"


@dataclass
class User:
    name: str
    id: int
    email: str
    role: UserRole = UserRole.CUSTOMER
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __str__(self):
        return f"User({self.id}) | {self.name} | {self.role.value} | {self.email}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at
        }

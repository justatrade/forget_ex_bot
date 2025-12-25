from decimal import Decimal
from pydantic import BaseModel


class Goods(BaseModel):
    name: str
    price: int | Decimal
    description: str


class DashasSpecial(Goods):
    code: str

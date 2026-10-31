
from decimal import Decimal

from pydantic import BaseModel, Field


class Produto(BaseModel):
    id: int
    nome: str
    categoria: str
    preco: Decimal
    estoque: int
    ativo: bool


class ProdutoCadastro(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    categoria: str = Field(min_length=3, max_length=50)
    preco: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2
    )
    estoque: int = Field(ge=0)

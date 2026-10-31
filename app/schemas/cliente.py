
from pydantic import BaseModel, EmailStr, Field


class ClienteCadastro(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    email: EmailStr
    telefone: str | None = Field(
        default=None,
        max_length=20
    )
    cpf: str | None = Field(
        default=None,
        pattern=r"^[0-9]{11}$"
    )
    senha: str | None = Field(
        default=None,
        min_length=8,
        max_length=128
    )


class Cliente(BaseModel):
    id: int
    nome: str
    email: EmailStr
    telefone: str | None
    cpf: str | None
    ativo: bool

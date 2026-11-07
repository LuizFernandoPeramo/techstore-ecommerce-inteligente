
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ItemCarrinhoCadastro(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class ItemCarrinhoAtualizacao(BaseModel):
    quantidade: int = Field(gt=0)


class ItemCarrinhoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal


class CarrinhoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    criado_em: datetime
    atualizado_em: datetime
    itens: list[ItemCarrinhoResposta]
    quantidade_itens: int
    valor_total: Decimal


from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ItemPedidoCadastro(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class PedidoCadastro(BaseModel):
    cliente_id: int = Field(gt=0)
    itens: list[ItemPedidoCadastro] = Field(min_length=1)


class ItemPedidoResposta(BaseModel):
    produto_id: int
    nome: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal


class PedidoResposta(BaseModel):
    id: int
    cliente_id: int
    status: str
    valor_total: Decimal
    itens: list[ItemPedidoResposta]


class PedidoAtualizacaoStatus(BaseModel):
    status: Literal[
        "pendente",
        "pago",
        "enviado",
        "entregue",
        "cancelado"
    ]

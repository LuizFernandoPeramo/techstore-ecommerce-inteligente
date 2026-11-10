
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


MetodoPagamento = Literal[
    "pix",
    "cartao",
    "boleto"
]

StatusPagamento = Literal[
    "pendente",
    "aprovado",
    "recusado",
    "cancelado"
]


class PagamentoCadastro(BaseModel):
    pedido_id: int = Field(gt=0)
    metodo: MetodoPagamento


class PagamentoSimulacao(BaseModel):
    resultado: Literal[
        "aprovado",
        "recusado"
    ]


class PagamentoResposta(BaseModel):
    id: int
    pedido_id: int
    valor: Decimal
    metodo: MetodoPagamento
    status: StatusPagamento
    referencia_externa: str | None = None
    criado_em: datetime
    atualizado_em: datetime


class PagamentoResultadoResposta(PagamentoResposta):
    mensagem: str

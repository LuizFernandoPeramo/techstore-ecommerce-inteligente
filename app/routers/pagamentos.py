
from fastapi import APIRouter, Depends, status

from app.core.permissions import exigir_administrador
from app.routers.auth import obter_cliente_autenticado
from app.schemas.pagamento import (
    PagamentoCadastro,
    PagamentoResposta,
    PagamentoResultadoResposta,
    PagamentoSimulacao
)
from app.services import pagamento_service


router = APIRouter(
    prefix="/pagamentos",
    tags=["Pagamentos"]
)


@router.post(
    "",
    response_model=PagamentoResposta,
    status_code=status.HTTP_201_CREATED
)
def criar_pagamento(
    dados: PagamentoCadastro,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return pagamento_service.criar_pagamento(
        dados=dados,
        cliente_autenticado=cliente_autenticado
    )


@router.post(
    "/{pagamento_id}/simular",
    response_model=PagamentoResultadoResposta
)
def simular_pagamento(
    pagamento_id: int,
    dados: PagamentoSimulacao,
    administrador: dict = Depends(exigir_administrador)
):
    return pagamento_service.simular_pagamento(
        pagamento_id=pagamento_id,
        resultado=dados.resultado
    )

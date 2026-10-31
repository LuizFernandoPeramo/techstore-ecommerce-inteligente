
from fastapi import APIRouter, status

from app.schemas.pedido import (
    PedidoCadastro,
    PedidoResposta,
    PedidoAtualizacaoStatus
)

from app.services import pedido_service


router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)


@router.post(
    "",
    response_model=PedidoResposta,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_pedido(pedido: PedidoCadastro):
    return pedido_service.cadastrar_pedido(pedido)


@router.get("")
def listar_pedidos():
    return pedido_service.listar_pedidos()


@router.get("/{pedido_id}")
def consultar_pedido(pedido_id: int):
    return pedido_service.consultar_pedido(pedido_id)


@router.patch("/{pedido_id}/status")
def atualizar_status_pedido(
    pedido_id: int,
    dados: PedidoAtualizacaoStatus
):
    return pedido_service.atualizar_status_pedido(
        pedido_id,
        dados.status
    )

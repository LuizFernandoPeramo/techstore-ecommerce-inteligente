
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.permissions import exigir_administrador
from app.routers.auth import obter_cliente_autenticado
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
def cadastrar_pedido(
    pedido: PedidoCadastro,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    if (
        cliente_autenticado["perfil"] != "admin"
        and cliente_autenticado["id"] != pedido.cliente_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao pode criar pedidos para outro cliente"
        )

    return pedido_service.cadastrar_pedido(pedido)


@router.get("")
def listar_pedidos(
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return pedido_service.listar_pedidos(
        cliente_autenticado=cliente_autenticado
    )


@router.get("/{pedido_id}")
def consultar_pedido(
    pedido_id: int,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return pedido_service.consultar_pedido(
        pedido_id=pedido_id,
        cliente_autenticado=cliente_autenticado
    )


@router.patch("/{pedido_id}/status")
def atualizar_status_pedido(
    pedido_id: int,
    dados: PedidoAtualizacaoStatus,
    administrador: dict = Depends(exigir_administrador)
):
    return pedido_service.atualizar_status_pedido(
        pedido_id,
        dados.status
    )

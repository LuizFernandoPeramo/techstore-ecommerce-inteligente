
from fastapi import APIRouter, Depends, status

from app.routers.auth import obter_cliente_autenticado
from app.schemas.carrinho import (
    CarrinhoResposta,
    ItemCarrinhoAtualizacao,
    ItemCarrinhoCadastro,
)
from app.services import carrinho_service


router = APIRouter(
    prefix="/carrinho",
    tags=["Carrinho"]
)


@router.get("", response_model=CarrinhoResposta)
def consultar_carrinho(
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return carrinho_service.consultar_carrinho(
        cliente_id=cliente_autenticado["id"]
    )


@router.post(
    "/itens",
    response_model=CarrinhoResposta,
    status_code=status.HTTP_200_OK
)
def adicionar_item(
    item: ItemCarrinhoCadastro,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return carrinho_service.adicionar_item(
        cliente_id=cliente_autenticado["id"],
        produto_id=item.produto_id,
        quantidade=item.quantidade
    )


@router.patch(
    "/itens/{produto_id}",
    response_model=CarrinhoResposta
)
def atualizar_item(
    produto_id: int,
    item: ItemCarrinhoAtualizacao,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return carrinho_service.atualizar_item(
        cliente_id=cliente_autenticado["id"],
        produto_id=produto_id,
        quantidade=item.quantidade
    )


@router.delete(
    "/itens/{produto_id}",
    response_model=CarrinhoResposta
)
def remover_item(
    produto_id: int,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return carrinho_service.remover_item(
        cliente_id=cliente_autenticado["id"],
        produto_id=produto_id
    )


@router.delete("", response_model=CarrinhoResposta)
def esvaziar_carrinho(
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    return carrinho_service.esvaziar_carrinho(
        cliente_id=cliente_autenticado["id"]
    )

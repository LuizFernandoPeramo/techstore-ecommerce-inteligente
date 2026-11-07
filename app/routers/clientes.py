
from fastapi import APIRouter, Depends, status

from app.core.permissions import (
    exigir_administrador,
    exigir_proprietario_ou_administrador
)
from app.schemas.cliente import Cliente, ClienteCadastro
from app.services import cliente_service


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.get("", response_model=list[Cliente])
def listar_clientes(
    administrador: dict = Depends(exigir_administrador)
):
    return cliente_service.listar_clientes()


@router.get("/{cliente_id}", response_model=Cliente)
def consultar_cliente(
    cliente_id: int,
    usuario: dict = Depends(
        exigir_proprietario_ou_administrador
    )
):
    return cliente_service.consultar_cliente(cliente_id)


@router.post(
    "",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_cliente(cliente: ClienteCadastro):
    return cliente_service.cadastrar_cliente(cliente)


@router.put("/{cliente_id}", response_model=Cliente)
def atualizar_cliente(
    cliente_id: int,
    cliente: ClienteCadastro,
    usuario: dict = Depends(
        exigir_proprietario_ou_administrador
    )
):
    return cliente_service.atualizar_cliente(
        cliente_id,
        cliente
    )


@router.delete("/{cliente_id}")
def excluir_cliente(
    cliente_id: int,
    usuario: dict = Depends(
        exigir_proprietario_ou_administrador
    )
):
    return cliente_service.excluir_cliente(cliente_id)

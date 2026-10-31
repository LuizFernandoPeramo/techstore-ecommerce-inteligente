
from fastapi import APIRouter, Depends, HTTPException, status

from app.routers.auth import obter_cliente_autenticado
from app.schemas.cliente import Cliente, ClienteCadastro
from app.services import cliente_service


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


def verificar_proprietario(
    cliente_id: int,
    cliente_autenticado: dict = Depends(
        obter_cliente_autenticado
    )
):
    if cliente_autenticado["id"] != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para alterar esta conta"
        )

    return cliente_autenticado


@router.get("", response_model=list[Cliente])
def listar_clientes():
    return cliente_service.listar_clientes()


@router.get("/{cliente_id}", response_model=Cliente)
def consultar_cliente(cliente_id: int):
    return cliente_service.consultar_cliente(cliente_id)


@router.post(
    "",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_cliente(cliente: ClienteCadastro):
    return cliente_service.cadastrar_cliente(cliente)


@router.put(
    "/{cliente_id}",
    response_model=Cliente
)
def atualizar_cliente(
    cliente_id: int,
    cliente: ClienteCadastro,
    cliente_autenticado: dict = Depends(
        verificar_proprietario
    )
):
    return cliente_service.atualizar_cliente(
        cliente_id,
        cliente
    )


@router.delete("/{cliente_id}")
def excluir_cliente(
    cliente_id: int,
    cliente_autenticado: dict = Depends(
        verificar_proprietario
    )
):
    return cliente_service.excluir_cliente(cliente_id)

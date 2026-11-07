
from fastapi import Depends, HTTPException, status

from app.routers.auth import obter_cliente_autenticado


def exigir_administrador(
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    if cliente_autenticado["perfil"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores"
        )

    return cliente_autenticado


def exigir_proprietario_ou_administrador(
    cliente_id: int,
    cliente_autenticado: dict = Depends(obter_cliente_autenticado)
):
    if (
        cliente_autenticado["id"] != cliente_id
        and cliente_autenticado["perfil"] != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para acessar esta conta"
        )

    return cliente_autenticado

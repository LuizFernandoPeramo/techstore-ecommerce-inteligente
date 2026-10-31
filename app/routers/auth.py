
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import validar_token_acesso
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.cliente import Cliente
from app.services import auth_service


router = APIRouter(
    prefix="/auth",
    tags=["Autenticacao"]
)

bearer_scheme = HTTPBearer()


def obter_cliente_autenticado(
    credenciais: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
):
    cliente_id = validar_token_acesso(
        credenciais.credentials
    )

    return auth_service.consultar_cliente_autenticado(
        cliente_id
    )


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(dados: LoginRequest):
    return auth_service.autenticar_cliente(
        email=dados.email,
        senha=dados.senha
    )


@router.get(
    "/me",
    response_model=Cliente
)
def consultar_meu_perfil(
    cliente: dict = Depends(obter_cliente_autenticado)
):
    return cliente

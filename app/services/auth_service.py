
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.core.security import (
    criar_token_acesso,
    verificar_senha
)


def autenticar_cliente(email: str, senha: str):
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        id,
                        nome,
                        email,
                        senha_hash,
                        ativo
                    FROM clientes
                    WHERE LOWER(email) = LOWER(:email)
                      AND ativo = TRUE
                """),
                {"email": email}
            )

            cliente = resultado.mappings().first()

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao autenticar cliente"
        )

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha invalidos",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if cliente is None:
        raise credenciais_invalidas

    if not cliente["senha_hash"]:
        raise credenciais_invalidas

    if not verificar_senha(
        senha,
        cliente["senha_hash"]
    ):
        raise credenciais_invalidas

    token = criar_token_acesso(cliente["id"])

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def consultar_cliente_autenticado(cliente_id: int):
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        id,
                        nome,
                        email,
                        telefone,
                        cpf,
                        ativo
                    FROM clientes
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                """),
                {"cliente_id": cliente_id}
            )

            cliente = resultado.mappings().first()

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar cliente autenticado"
        )

    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cliente nao autenticado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return dict(cliente)

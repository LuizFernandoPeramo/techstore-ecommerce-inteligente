
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import engine
from app.schemas.cliente import ClienteCadastro


def cadastrar_cliente(cliente: ClienteCadastro):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    INSERT INTO clientes (
                        nome, email, telefone, cpf
                    )
                    VALUES (
                        :nome, :email, :telefone, :cpf
                    )
                    RETURNING
                        id, nome, email, telefone, cpf, ativo
                """),
                cliente.model_dump()
            )

            return dict(resultado.mappings().one())

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Email ou CPF ja cadastrado"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar cliente"
        )


def listar_clientes():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        id, nome, email, telefone, cpf, ativo
                    FROM clientes
                    WHERE ativo = TRUE
                    ORDER BY id
                """)
            )

            return [
                dict(linha)
                for linha in resultado.mappings().all()
            ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar clientes"
        )


def consultar_cliente(cliente_id: int):
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        id, nome, email, telefone, cpf, ativo
                    FROM clientes
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                """),
                {"cliente_id": cliente_id}
            )

            cliente = resultado.mappings().first()

            if cliente is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente nao encontrado"
                )

            return dict(cliente)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar cliente"
        )


def atualizar_cliente(cliente_id: int, cliente: ClienteCadastro):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    UPDATE clientes
                    SET
                        nome = :nome,
                        email = :email,
                        telefone = :telefone,
                        cpf = :cpf,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                    RETURNING
                        id, nome, email, telefone, cpf, ativo
                """),
                {
                    **cliente.model_dump(),
                    "cliente_id": cliente_id
                }
            )

            cliente_atualizado = resultado.mappings().first()

            if cliente_atualizado is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente nao encontrado"
                )

            return dict(cliente_atualizado)

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Email ou CPF ja cadastrado"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar cliente"
        )


def excluir_cliente(cliente_id: int):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    UPDATE clientes
                    SET
                        ativo = FALSE,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                    RETURNING id, nome
                """),
                {"cliente_id": cliente_id}
            )

            cliente_excluido = resultado.mappings().first()

            if cliente_excluido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente nao encontrado ou ja inativo"
                )

            return {
                "mensagem": "Cliente desativado com sucesso",
                "id": cliente_excluido["id"],
                "nome": cliente_excluido["nome"]
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao desativar cliente"
        )

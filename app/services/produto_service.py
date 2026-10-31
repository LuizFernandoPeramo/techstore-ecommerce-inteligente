
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import engine
from app.schemas.produto import ProdutoCadastro


def listar_produtos():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT id, nome, categoria, preco, estoque, ativo
                    FROM produtos
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
            detail="Erro ao consultar produtos"
        )


def consultar_produto(produto_id: int):
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT id, nome, categoria, preco, estoque, ativo
                    FROM produtos
                    WHERE id = :produto_id
                      AND ativo = TRUE
                """),
                {"produto_id": produto_id}
            )

            produto = resultado.mappings().first()

            if produto is None:
                raise HTTPException(
                    status_code=404,
                    detail="Produto nao encontrado"
                )

            return dict(produto)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar produto"
        )


def cadastrar_produto(produto: ProdutoCadastro):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    INSERT INTO produtos (
                        nome, categoria, preco, estoque
                    )
                    VALUES (
                        :nome, :categoria, :preco, :estoque
                    )
                    RETURNING id, nome, categoria, preco, estoque, ativo
                """),
                produto.model_dump()
            )

            return dict(resultado.mappings().one())

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Nao foi possivel cadastrar o produto"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar produto"
        )


def atualizar_produto(produto_id: int, produto: ProdutoCadastro):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    UPDATE produtos
                    SET
                        nome = :nome,
                        categoria = :categoria,
                        preco = :preco,
                        estoque = :estoque
                    WHERE id = :produto_id
                      AND ativo = TRUE
                    RETURNING id, nome, categoria, preco, estoque, ativo
                """),
                {
                    **produto.model_dump(),
                    "produto_id": produto_id
                }
            )

            produto_atualizado = resultado.mappings().first()

            if produto_atualizado is None:
                raise HTTPException(
                    status_code=404,
                    detail="Produto nao encontrado"
                )

            return dict(produto_atualizado)

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Nao foi possivel atualizar o produto"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar produto"
        )


def excluir_produto(produto_id: int):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    UPDATE produtos
                    SET ativo = FALSE
                    WHERE id = :produto_id
                      AND ativo = TRUE
                    RETURNING id, nome
                """),
                {"produto_id": produto_id}
            )

            produto_excluido = resultado.mappings().first()

            if produto_excluido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Produto nao encontrado ou ja inativo"
                )

            return {
                "mensagem": "Produto desativado com sucesso",
                "id": produto_excluido["id"],
                "nome": produto_excluido["nome"]
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao desativar produto"
        )

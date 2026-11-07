
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


def _obter_carrinho(conexao, cliente_id: int):
    resultado = conexao.execute(
        text("""
            INSERT INTO carrinhos (cliente_id)
            VALUES (:cliente_id)
            ON CONFLICT (cliente_id)
            DO UPDATE SET cliente_id = EXCLUDED.cliente_id
            RETURNING id, cliente_id, criado_em, atualizado_em
        """),
        {"cliente_id": cliente_id}
    )

    return dict(resultado.mappings().one())


def _consultar_carrinho(conexao, cliente_id: int):
    carrinho = _obter_carrinho(conexao, cliente_id)

    resultado = conexao.execute(
        text("""
            SELECT
                ic.id,
                ic.produto_id,
                p.nome AS produto_nome,
                ic.quantidade,
                p.preco AS preco_unitario,
                ic.quantidade * p.preco AS subtotal
            FROM itens_carrinho ic
            INNER JOIN produtos p
                ON p.id = ic.produto_id
            WHERE ic.carrinho_id = :carrinho_id
            ORDER BY ic.id
        """),
        {"carrinho_id": carrinho["id"]}
    )

    itens = [
        dict(item)
        for item in resultado.mappings().all()
    ]

    valor_total = sum(
        (item["subtotal"] for item in itens),
        Decimal("0.00")
    )

    quantidade_itens = sum(
        item["quantidade"]
        for item in itens
    )

    return {
        **carrinho,
        "itens": itens,
        "quantidade_itens": quantidade_itens,
        "valor_total": valor_total
    }


def _validar_produto(conexao, produto_id: int, quantidade: int):
    produto = conexao.execute(
        text("""
            SELECT id, nome, preco, estoque
            FROM produtos
            WHERE id = :produto_id
              AND ativo = TRUE
            FOR UPDATE
        """),
        {"produto_id": produto_id}
    ).mappings().first()

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto nao encontrado ou inativo"
        )

    if produto["estoque"] < quantidade:
        raise HTTPException(
            status_code=409,
            detail="Estoque insuficiente para a quantidade solicitada"
        )

    return dict(produto)


def consultar_carrinho(cliente_id: int):
    try:
        with engine.begin() as conexao:
            return _consultar_carrinho(conexao, cliente_id)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar carrinho"
        )


def adicionar_item(cliente_id: int, produto_id: int, quantidade: int):
    if quantidade <= 0:
        raise HTTPException(
            status_code=422,
            detail="A quantidade deve ser maior que zero"
        )

    try:
        with engine.begin() as conexao:
            carrinho = _obter_carrinho(conexao, cliente_id)

            item_atual = conexao.execute(
                text("""
                    SELECT quantidade
                    FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                      AND produto_id = :produto_id
                """),
                {
                    "carrinho_id": carrinho["id"],
                    "produto_id": produto_id
                }
            ).mappings().first()

            quantidade_atual = (
                item_atual["quantidade"]
                if item_atual is not None
                else 0
            )

            nova_quantidade = quantidade_atual + quantidade

            _validar_produto(
                conexao,
                produto_id,
                nova_quantidade
            )

            conexao.execute(
                text("""
                    INSERT INTO itens_carrinho (
                        carrinho_id,
                        produto_id,
                        quantidade
                    )
                    VALUES (
                        :carrinho_id,
                        :produto_id,
                        :quantidade
                    )
                    ON CONFLICT (carrinho_id, produto_id)
                    DO UPDATE SET quantidade = :nova_quantidade
                """),
                {
                    "carrinho_id": carrinho["id"],
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                    "nova_quantidade": nova_quantidade
                }
            )

            conexao.execute(
                text("""
                    UPDATE carrinhos
                    SET atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :carrinho_id
                """),
                {"carrinho_id": carrinho["id"]}
            )

            return _consultar_carrinho(conexao, cliente_id)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao adicionar produto ao carrinho"
        )


def atualizar_item(cliente_id: int, produto_id: int, quantidade: int):
    if quantidade <= 0:
        raise HTTPException(
            status_code=422,
            detail="A quantidade deve ser maior que zero"
        )

    try:
        with engine.begin() as conexao:
            carrinho = _obter_carrinho(conexao, cliente_id)

            item = conexao.execute(
                text("""
                    SELECT id
                    FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                      AND produto_id = :produto_id
                """),
                {
                    "carrinho_id": carrinho["id"],
                    "produto_id": produto_id
                }
            ).mappings().first()

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Produto nao encontrado no carrinho"
                )

            _validar_produto(
                conexao,
                produto_id,
                quantidade
            )

            conexao.execute(
                text("""
                    UPDATE itens_carrinho
                    SET quantidade = :quantidade
                    WHERE id = :item_id
                """),
                {
                    "quantidade": quantidade,
                    "item_id": item["id"]
                }
            )

            conexao.execute(
                text("""
                    UPDATE carrinhos
                    SET atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :carrinho_id
                """),
                {"carrinho_id": carrinho["id"]}
            )

            return _consultar_carrinho(conexao, cliente_id)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar produto no carrinho"
        )


def remover_item(cliente_id: int, produto_id: int):
    try:
        with engine.begin() as conexao:
            carrinho = _obter_carrinho(conexao, cliente_id)

            resultado = conexao.execute(
                text("""
                    DELETE FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                      AND produto_id = :produto_id
                    RETURNING id
                """),
                {
                    "carrinho_id": carrinho["id"],
                    "produto_id": produto_id
                }
            )

            if resultado.mappings().first() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Produto nao encontrado no carrinho"
                )

            conexao.execute(
                text("""
                    UPDATE carrinhos
                    SET atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :carrinho_id
                """),
                {"carrinho_id": carrinho["id"]}
            )

            return _consultar_carrinho(conexao, cliente_id)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao remover produto do carrinho"
        )


def esvaziar_carrinho(cliente_id: int):
    try:
        with engine.begin() as conexao:
            carrinho = _obter_carrinho(conexao, cliente_id)

            conexao.execute(
                text("""
                    DELETE FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                """),
                {"carrinho_id": carrinho["id"]}
            )

            conexao.execute(
                text("""
                    UPDATE carrinhos
                    SET atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :carrinho_id
                """),
                {"carrinho_id": carrinho["id"]}
            )

            return _consultar_carrinho(conexao, cliente_id)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao esvaziar carrinho"
        )

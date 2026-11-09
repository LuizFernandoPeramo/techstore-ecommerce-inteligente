
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


def finalizar_compra(cliente_id: int):
    try:
        with engine.begin() as conexao:
            cliente = conexao.execute(
                text("""
                    SELECT id
                    FROM clientes
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                """),
                {"cliente_id": cliente_id}
            ).mappings().first()

            if cliente is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente nao encontrado ou inativo"
                )

            carrinho = conexao.execute(
                text("""
                    SELECT id
                    FROM carrinhos
                    WHERE cliente_id = :cliente_id
                    FOR UPDATE
                """),
                {"cliente_id": cliente_id}
            ).mappings().first()

            if carrinho is None:
                raise HTTPException(
                    status_code=409,
                    detail="O carrinho esta vazio"
                )

            carrinho_id = carrinho["id"]

            itens_carrinho = conexao.execute(
                text("""
                    SELECT produto_id, quantidade
                    FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                    ORDER BY produto_id
                """),
                {"carrinho_id": carrinho_id}
            ).mappings().all()

            if not itens_carrinho:
                raise HTTPException(
                    status_code=409,
                    detail="O carrinho esta vazio"
                )

            ids_produtos = [
                item["produto_id"]
                for item in itens_carrinho
            ]

            produtos = conexao.execute(
                text("""
                    SELECT id, nome, preco, estoque
                    FROM produtos
                    WHERE id = ANY(:ids_produtos)
                      AND ativo = TRUE
                    ORDER BY id
                    FOR UPDATE
                """),
                {"ids_produtos": ids_produtos}
            ).mappings().all()

            produtos_por_id = {
                produto["id"]: produto
                for produto in produtos
            }

            itens_calculados = []
            valor_total = Decimal("0.00")

            for item in itens_carrinho:
                produto_id = item["produto_id"]
                quantidade = item["quantidade"]
                produto = produtos_por_id.get(produto_id)

                if produto is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Produto {produto_id} "
                            "nao encontrado ou inativo"
                        )
                    )

                if produto["estoque"] < quantidade:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Estoque insuficiente para o "
                            f"produto {produto_id}"
                        )
                    )

                preco_unitario = produto["preco"]
                subtotal = preco_unitario * quantidade

                valor_total += subtotal

                itens_calculados.append({
                    "produto_id": produto_id,
                    "nome": produto["nome"],
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                    "subtotal": subtotal
                })

            resultado = conexao.execute(
                text("""
                    INSERT INTO pedidos (
                        cliente_id,
                        status,
                        valor_total
                    )
                    VALUES (
                        :cliente_id,
                        'pendente',
                        :valor_total
                    )
                    RETURNING
                        id,
                        cliente_id,
                        status,
                        valor_total
                """),
                {
                    "cliente_id": cliente_id,
                    "valor_total": valor_total
                }
            )

            pedido_criado = dict(
                resultado.mappings().one()
            )

            for item in itens_calculados:
                conexao.execute(
                    text("""
                        INSERT INTO itens_pedido (
                            pedido_id,
                            produto_id,
                            quantidade,
                            preco_unitario
                        )
                        VALUES (
                            :pedido_id,
                            :produto_id,
                            :quantidade,
                            :preco_unitario
                        )
                    """),
                    {
                        "pedido_id": pedido_criado["id"],
                        "produto_id": item["produto_id"],
                        "quantidade": item["quantidade"],
                        "preco_unitario": item["preco_unitario"]
                    }
                )

                conexao.execute(
                    text("""
                        UPDATE produtos
                        SET estoque = estoque - :quantidade
                        WHERE id = :produto_id
                    """),
                    {
                        "quantidade": item["quantidade"],
                        "produto_id": item["produto_id"]
                    }
                )

            conexao.execute(
                text("""
                    DELETE FROM itens_carrinho
                    WHERE carrinho_id = :carrinho_id
                """),
                {"carrinho_id": carrinho_id}
            )

            conexao.execute(
                text("""
                    UPDATE carrinhos
                    SET atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :carrinho_id
                """),
                {"carrinho_id": carrinho_id}
            )

            return {
                **pedido_criado,
                "itens": itens_calculados
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao finalizar compra"
        )

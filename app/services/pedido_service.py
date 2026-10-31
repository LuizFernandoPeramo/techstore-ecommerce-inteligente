
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.schemas.pedido import PedidoCadastro


TRANSICOES_PERMITIDAS = {
    "pendente": {"pago", "cancelado"},
    "pago": {"enviado", "cancelado"},
    "enviado": {"entregue"},
    "entregue": set(),
    "cancelado": set()
}


def cadastrar_pedido(pedido: PedidoCadastro):
    ids_produtos = [item.produto_id for item in pedido.itens]

    if len(ids_produtos) != len(set(ids_produtos)):
        raise HTTPException(
            status_code=422,
            detail="O mesmo produto nao pode aparecer duas vezes no pedido"
        )

    try:
        with engine.begin() as conexao:
            cliente = conexao.execute(
                text("""
                    SELECT id
                    FROM clientes
                    WHERE id = :cliente_id
                      AND ativo = TRUE
                """),
                {"cliente_id": pedido.cliente_id}
            ).mappings().first()

            if cliente is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente nao encontrado ou inativo"
                )

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

            for item in pedido.itens:
                produto = produtos_por_id.get(item.produto_id)

                if produto is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Produto {item.produto_id} "
                            "nao encontrado ou inativo"
                        )
                    )

                if produto["estoque"] < item.quantidade:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Estoque insuficiente para o "
                            f"produto {item.produto_id}"
                        )
                    )

                preco_unitario = produto["preco"]
                subtotal = preco_unitario * item.quantidade

                valor_total += subtotal

                itens_calculados.append({
                    "produto_id": item.produto_id,
                    "nome": produto["nome"],
                    "quantidade": item.quantidade,
                    "preco_unitario": preco_unitario,
                    "subtotal": subtotal
                })

            resultado_pedido = conexao.execute(
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
                    "cliente_id": pedido.cliente_id,
                    "valor_total": valor_total
                }
            )

            pedido_criado = dict(
                resultado_pedido.mappings().one()
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

            return {
                **pedido_criado,
                "itens": itens_calculados
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao registrar pedido"
        )


def listar_pedidos():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        p.id,
                        p.cliente_id,
                        c.nome AS cliente_nome,
                        p.data_pedido,
                        p.status,
                        p.valor_total
                    FROM pedidos p
                    INNER JOIN clientes c
                        ON c.id = p.cliente_id
                    ORDER BY p.id DESC
                """)
            )

            return [
                dict(pedido)
                for pedido in resultado.mappings().all()
            ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao listar pedidos"
        )


def consultar_pedido(pedido_id: int):
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        p.id,
                        p.cliente_id,
                        c.nome AS cliente_nome,
                        p.data_pedido,
                        p.status,
                        p.valor_total
                    FROM pedidos p
                    INNER JOIN clientes c
                        ON c.id = p.cliente_id
                    WHERE p.id = :pedido_id
                """),
                {"pedido_id": pedido_id}
            )

            pedido = resultado.mappings().first()

            if pedido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pedido nao encontrado"
                )

            resultado_itens = conexao.execute(
                text("""
                    SELECT
                        ip.produto_id,
                        pr.nome,
                        ip.quantidade,
                        ip.preco_unitario,
                        ip.subtotal
                    FROM itens_pedido ip
                    INNER JOIN produtos pr
                        ON pr.id = ip.produto_id
                    WHERE ip.pedido_id = :pedido_id
                    ORDER BY ip.id
                """),
                {"pedido_id": pedido_id}
            )

            itens = [
                dict(item)
                for item in resultado_itens.mappings().all()
            ]

            return {
                **dict(pedido),
                "itens": itens
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar pedido"
        )


def atualizar_status_pedido(pedido_id: int, novo_status: str):
    try:
        with engine.begin() as conexao:
            resultado = conexao.execute(
                text("""
                    SELECT
                        id,
                        cliente_id,
                        status,
                        valor_total
                    FROM pedidos
                    WHERE id = :pedido_id
                    FOR UPDATE
                """),
                {"pedido_id": pedido_id}
            )

            pedido = resultado.mappings().first()

            if pedido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pedido nao encontrado"
                )

            status_atual = pedido["status"]

            if novo_status == status_atual:
                raise HTTPException(
                    status_code=409,
                    detail="O pedido ja possui este status"
                )

            status_permitidos = TRANSICOES_PERMITIDAS.get(
                status_atual,
                set()
            )

            if novo_status not in status_permitidos:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Nao e permitido alterar o pedido "
                        f"de '{status_atual}' para '{novo_status}'"
                    )
                )

            if novo_status == "cancelado":
                itens = conexao.execute(
                    text("""
                        SELECT produto_id, quantidade
                        FROM itens_pedido
                        WHERE pedido_id = :pedido_id
                        ORDER BY produto_id
                    """),
                    {"pedido_id": pedido_id}
                ).mappings().all()

                for item in itens:
                    conexao.execute(
                        text("""
                            UPDATE produtos
                            SET estoque = estoque + :quantidade
                            WHERE id = :produto_id
                        """),
                        {
                            "quantidade": item["quantidade"],
                            "produto_id": item["produto_id"]
                        }
                    )

            resultado_atualizacao = conexao.execute(
                text("""
                    UPDATE pedidos
                    SET status = :novo_status
                    WHERE id = :pedido_id
                    RETURNING
                        id,
                        cliente_id,
                        status,
                        valor_total
                """),
                {
                    "novo_status": novo_status,
                    "pedido_id": pedido_id
                }
            )

            pedido_atualizado = dict(
                resultado_atualizacao.mappings().one()
            )

            return {
                **pedido_atualizado,
                "mensagem": "Status do pedido atualizado com sucesso"
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar status do pedido"
        )


from decimal import Decimal

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError


def test_checkout_desfaz_transacao_em_falha(
    client,
    banco_limpo,
    test_engine
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Cliente Teste Rollback",
            "email": "rollback@exemplo.com",
            "telefone": "11999998888",
            "cpf": "00000001001",
            "senha": "TechStore@2026"
        }
    )

    assert resposta_cliente.status_code == 201, (
        resposta_cliente.text
    )

    cliente_id = resposta_cliente.json()["id"]

    resposta_login = client.post(
        "/auth/login",
        json={
            "email": "rollback@exemplo.com",
            "senha": "TechStore@2026"
        }
    )

    assert resposta_login.status_code == 200, (
        resposta_login.text
    )

    headers = {
        "Authorization": (
            f"Bearer {resposta_login.json()['access_token']}"
        )
    }

    with test_engine.begin() as conexao:
        produto_id = conexao.execute(
            text("""
                INSERT INTO produtos (
                    nome,
                    categoria,
                    preco,
                    estoque
                )
                VALUES (
                    'Produto Rollback',
                    'Eletronicos',
                    150.00,
                    10
                )
                RETURNING id
            """)
        ).scalar_one()

    resposta_carrinho = client.post(
        "/carrinho/itens",
        headers=headers,
        json={
            "produto_id": produto_id,
            "quantidade": 3
        }
    )

    assert resposta_carrinho.status_code == 200, (
        resposta_carrinho.text
    )

    def simular_falha(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany
    ):
        comando = " ".join(statement.lower().split())

        if "delete from itens_carrinho" in comando:
            raise SQLAlchemyError(
                "Falha simulada durante o checkout"
            )

    event.listen(
        test_engine,
        "before_cursor_execute",
        simular_falha
    )

    try:
        resposta_checkout = client.post(
            "/carrinho/checkout",
            headers=headers
        )

        assert resposta_checkout.status_code == 500, (
            resposta_checkout.text
        )

    finally:
        event.remove(
            test_engine,
            "before_cursor_execute",
            simular_falha
        )

    with test_engine.connect() as conexao:
        pedidos = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM pedidos
                WHERE cliente_id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).scalar_one()

        itens_pedido = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM itens_pedido
            """)
        ).scalar_one()

        estoque = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

        itens_carrinho = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM itens_carrinho ic
                INNER JOIN carrinhos c
                    ON c.id = ic.carrinho_id
                WHERE c.cliente_id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).scalar_one()

    assert pedidos == 0
    assert itens_pedido == 0
    assert estoque == 10
    assert itens_carrinho == 1

    resposta_consulta = client.get(
        "/carrinho",
        headers=headers
    )

    assert resposta_consulta.status_code == 200
    assert resposta_consulta.json()["quantidade_itens"] == 3

    resposta_novo_checkout = client.post(
        "/carrinho/checkout",
        headers=headers
    )

    assert resposta_novo_checkout.status_code == 201, (
        resposta_novo_checkout.text
    )

    assert Decimal(
        str(resposta_novo_checkout.json()["valor_total"])
    ) == Decimal("450.00")

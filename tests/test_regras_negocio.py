from decimal import Decimal

import pytest
from sqlalchemy import text


@pytest.fixture
def headers_admin_regras(client, test_engine, banco_limpo):
    senha = "TechStore@2026"
    email = "admin.regras@exemplo.com"

    resposta = client.post(
        "/clientes",
        json={
            "nome": "Administrador Regras",
            "email": email,
            "telefone": "11999998888",
            "cpf": "99999999999",
            "senha": senha
        }
    )
    assert resposta.status_code == 201, resposta.text
    administrador_id = resposta.json()["id"]

    with test_engine.begin() as conexao:
        banco = conexao.execute(text("SELECT current_database()" )).scalar_one()
        if banco != "techstore_test_db":
            raise RuntimeError("Banco de testes incorreto")
        atualizado = conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'admin'
                WHERE id = :cliente_id AND perfil = 'cliente'
                RETURNING id
            """),
            {"cliente_id": administrador_id}
        ).scalar_one()
        assert atualizado == administrador_id

    login = client.post(
        "/auth/login",
        json={"email": email, "senha": senha}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def criar_cliente(client, numero=1):
    resposta = client.post(
        "/clientes",
        json={
            "nome": f"Cliente Teste {numero}",
            "email": f"cliente{numero}@exemplo.com",
            "telefone": "11999998888",
            "cpf": f"{numero:011d}"
        }
    )

    assert resposta.status_code == 201
    return resposta.json()["id"]


def criar_produto(client, headers_admin_regras, numero=1, estoque=10):
    resposta = client.post(
        "/produtos",
        json={
            "nome": f"Produto Teste {numero}",
            "categoria": "Informatica",
            "preco": "150.00",
            "estoque": estoque
        },
        headers=headers_admin_regras
    )

    assert resposta.status_code == 201
    return resposta.json()["id"]


def criar_pedido(client, cliente_id, produto_id, quantidade=1):
    return client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": quantidade
                }
            ]
        }
    )


def consultar_estoque(test_engine, produto_id):
    with test_engine.connect() as conexao:
        return conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()


def test_cliente_email_duplicado(client, banco_limpo):
    criar_cliente(client)

    resposta = client.post(
        "/clientes",
        json={
            "nome": "Outro Cliente",
            "email": "cliente1@exemplo.com",
            "telefone": "11988887777",
            "cpf": "12345678901"
        }
    )

    assert resposta.status_code == 409


def test_cliente_cpf_duplicado(client, banco_limpo):
    criar_cliente(client)

    resposta = client.post(
        "/clientes",
        json={
            "nome": "Outro Cliente",
            "email": "outro@exemplo.com",
            "telefone": "11988887777",
            "cpf": "00000000001"
        }
    )

    assert resposta.status_code == 409


@pytest.mark.parametrize(
    "dados_invalidos",
    [
        {
            "nome": "AB",
            "email": "teste1@exemplo.com",
            "cpf": "12345678901"
        },
        {
            "nome": "Cliente Valido",
            "email": "email-invalido",
            "cpf": "12345678901"
        },
        {
            "nome": "Cliente Valido",
            "email": "teste2@exemplo.com",
            "cpf": "123"
        },
        {
            "nome": "Cliente Valido",
            "email": "teste3@exemplo.com",
            "cpf": "abcdefghijk"
        },
        {
            "nome": "Cliente Valido",
            "email": "teste4@exemplo.com",
            "cpf": "123456789012"
        }
    ]
)
def test_validacao_dados_cliente(
    client,
    banco_limpo,
    dados_invalidos
):
    resposta = client.post(
        "/clientes",
        json=dados_invalidos
    )

    assert resposta.status_code == 422


def test_pedido_com_produto_duplicado(
    client,
    test_engine,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)
    produto_id = criar_produto(client, headers_admin_regras, estoque=10)

    resposta = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 2
                },
                {
                    "produto_id": produto_id,
                    "quantidade": 3
                }
            ]
        }
    )

    assert resposta.status_code == 422
    assert consultar_estoque(test_engine, produto_id) == 10

    with test_engine.connect() as conexao:
        total_pedidos = conexao.execute(
            text("SELECT COUNT(*) FROM pedidos")
        ).scalar_one()

    assert total_pedidos == 0


@pytest.mark.parametrize(
    "pedido_invalido",
    [
        {
            "cliente_id": 1,
            "itens": []
        },
        {
            "cliente_id": 0,
            "itens": [
                {"produto_id": 1, "quantidade": 1}
            ]
        },
        {
            "cliente_id": 1,
            "itens": [
                {"produto_id": 0, "quantidade": 1}
            ]
        },
        {
            "cliente_id": 1,
            "itens": [
                {"produto_id": 1, "quantidade": 0}
            ]
        },
        {
            "cliente_id": 1,
            "itens": [
                {"produto_id": 1, "quantidade": -2}
            ]
        }
    ]
)
def test_validacao_dados_pedido(
    client,
    banco_limpo,
    pedido_invalido
):
    resposta = client.post(
        "/pedidos",
        json=pedido_invalido
    )

    assert resposta.status_code == 422


def test_cancelamento_pedido_pago_devolve_estoque(
    client,
    test_engine,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)
    produto_id = criar_produto(client, headers_admin_regras, estoque=10)

    resposta_pedido = criar_pedido(
        client,
        cliente_id,
        produto_id,
        quantidade=4
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    assert consultar_estoque(test_engine, produto_id) == 6

    resposta_pagamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "pago"}
    )

    assert resposta_pagamento.status_code == 200

    resposta_cancelamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_cancelamento.status_code == 200
    assert resposta_cancelamento.json()["status"] == "cancelado"
    assert consultar_estoque(test_engine, produto_id) == 10


def test_pedido_enviado_nao_pode_ser_cancelado(
    client,
    test_engine,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)
    produto_id = criar_produto(client, headers_admin_regras, estoque=10)

    resposta_pedido = criar_pedido(
        client,
        cliente_id,
        produto_id,
        quantidade=2
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    for status in ["pago", "enviado"]:
        resposta = client.patch(
            f"/pedidos/{pedido_id}/status",
            json={"status": status}
        )
        assert resposta.status_code == 200

    resposta_cancelamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_cancelamento.status_code == 409
    assert consultar_estoque(test_engine, produto_id) == 8

    resposta_consulta = client.get(f"/pedidos/{pedido_id}")

    assert resposta_consulta.status_code == 200
    assert resposta_consulta.json()["status"] == "enviado"


def test_status_pedido_inexistente(client, banco_limpo):
    resposta = client.patch(
        "/pedidos/99999/status",
        json={"status": "pago"}
    )

    assert resposta.status_code == 404


def test_pedido_cancelado_nao_pode_ser_reativado(
    client,
    test_engine,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)
    produto_id = criar_produto(client, headers_admin_regras, estoque=5)

    resposta_pedido = criar_pedido(
        client,
        cliente_id,
        produto_id,
        quantidade=2
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    resposta_cancelamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_cancelamento.status_code == 200

    resposta_reativacao = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "pago"}
    )

    assert resposta_reativacao.status_code == 409
    assert consultar_estoque(test_engine, produto_id) == 5


def test_total_pedido_com_multiplos_produtos(
    client,
    test_engine,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)

    produto_1 = criar_produto(client, headers_admin_regras, numero=1, estoque=10)
    produto_2 = criar_produto(client, headers_admin_regras, numero=2, estoque=10)

    resposta = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_1,
                    "quantidade": 2
                },
                {
                    "produto_id": produto_2,
                    "quantidade": 3
                }
            ]
        }
    )

    assert resposta.status_code == 201
    assert Decimal(str(resposta.json()["valor_total"])) == Decimal("750.00")

    assert consultar_estoque(test_engine, produto_1) == 8
    assert consultar_estoque(test_engine, produto_2) == 7


def test_exclusao_logica_preserva_historico_pedido(
    client,
    banco_limpo,
    headers_admin_regras
):
    cliente_id = criar_cliente(client)
    produto_id = criar_produto(client, headers_admin_regras)

    resposta_pedido = criar_pedido(
        client,
        cliente_id,
        produto_id
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    resposta_exclusao = client.delete(
        f"/produtos/{produto_id}",
        headers=headers_admin_regras
    )

    assert resposta_exclusao.status_code == 200

    resposta_consulta = client.get(
        f"/pedidos/{pedido_id}"
    )

    assert resposta_consulta.status_code == 200
    assert resposta_consulta.json()["id"] == pedido_id
    assert len(resposta_consulta.json()["itens"]) == 1

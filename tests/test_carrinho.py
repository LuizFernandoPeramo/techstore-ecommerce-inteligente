from decimal import Decimal

import pytest
from sqlalchemy import text

SENHA = "TechStore@2026"


def cadastrar_cliente(client, numero):
    resposta = client.post(
        "/clientes",
        json={
            "nome": f"Cliente Carrinho {numero}",
            "email": f"carrinho{numero}@exemplo.com",
            "telefone": "11999998888",
            "cpf": f"{numero:011d}",
            "senha": SENHA,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autenticar(client, cliente):
    resposta = client.post(
        "/auth/login",
        json={"email": cliente["email"], "senha": SENHA},
    )
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def contexto_carrinho(client, test_engine, banco_limpo):
    cliente_1 = cadastrar_cliente(client, 201)
    cliente_2 = cadastrar_cliente(client, 202)
    administrador = cadastrar_cliente(client, 203)

    with test_engine.begin() as conexao:
        banco = conexao.execute(text("SELECT current_database() ")).scalar_one()
        assert banco == "techstore_test_db"
        conexao.execute(
            text("UPDATE clientes SET perfil = 'admin' WHERE id = :id"),
            {"id": administrador["id"]},
        )

    headers_admin = autenticar(client, administrador)
    produto = client.post(
        "/produtos",
        json={
            "nome": "Teclado Carrinho",
            "categoria": "Perifericos",
            "preco": "50.00",
            "estoque": 10,
        },
        headers=headers_admin,
    )
    assert produto.status_code == 201, produto.text

    produto_2 = client.post(
        "/produtos",
        json={
            "nome": "Mouse Carrinho",
            "categoria": "Perifericos",
            "preco": "25.50",
            "estoque": 5,
        },
        headers=headers_admin,
    )
    assert produto_2.status_code == 201, produto_2.text

    return {
        "cliente_1": cliente_1,
        "cliente_2": cliente_2,
        "headers_1": autenticar(client, cliente_1),
        "headers_2": autenticar(client, cliente_2),
        "headers_admin": headers_admin,
        "produto_id": produto.json()["id"],
        "produto_2_id": produto_2.json()["id"],
    }


def adicionar(client, contexto, quantidade=1, produto_id=None, headers=None):
    return client.post(
        "/carrinho/itens",
        json={
            "produto_id": produto_id or contexto["produto_id"],
            "quantidade": quantidade,
        },
        headers=headers or contexto["headers_1"],
    )


@pytest.mark.parametrize(
    "metodo,rota",
    [
        ("get", "/carrinho"),
        ("post", "/carrinho/itens"),
        ("patch", "/carrinho/itens/1"),
        ("delete", "/carrinho/itens/1"),
        ("delete", "/carrinho"),
    ],
)
def test_carrinho_exige_autenticacao(client, contexto_carrinho, metodo, rota):
    resposta = getattr(client, metodo)(rota)
    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "metodo,rota",
    [
        ("get", "/carrinho"),
        ("post", "/carrinho/itens"),
        ("patch", "/carrinho/itens/1"),
        ("delete", "/carrinho/itens/1"),
        ("delete", "/carrinho"),
    ],
)
def test_carrinho_rejeita_token_invalido(client, contexto_carrinho, metodo, rota):
    resposta = getattr(client, metodo)(
        rota, headers={"Authorization": "Bearer token-invalido"}
    )
    assert resposta.status_code == 401


def test_carrinho_vazio(client, contexto_carrinho):
    resposta = client.get("/carrinho", headers=contexto_carrinho["headers_1"])
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["cliente_id"] == contexto_carrinho["cliente_1"]["id"]
    assert dados["itens"] == []
    assert dados["quantidade_itens"] == 0
    assert Decimal(str(dados["valor_total"])) == Decimal("0.00")


def test_adicionar_produto_e_calcular_total(client, contexto_carrinho):
    resposta = adicionar(client, contexto_carrinho, quantidade=2)
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["quantidade_itens"] == 2
    assert len(dados["itens"]) == 1
    assert dados["itens"][0]["produto_nome"] == "Teclado Carrinho"
    assert Decimal(str(dados["itens"][0]["subtotal"])) == Decimal("100.00")
    assert Decimal(str(dados["valor_total"])) == Decimal("100.00")


def test_adicionar_mesmo_produto_soma_quantidade(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho, quantidade=2).status_code == 200
    resposta = adicionar(client, contexto_carrinho, quantidade=3)
    assert resposta.status_code == 200, resposta.text
    assert len(resposta.json()["itens"]) == 1
    assert resposta.json()["itens"][0]["quantidade"] == 5


def test_adicionar_produtos_diferentes(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho, quantidade=2).status_code == 200
    resposta = adicionar(
        client, contexto_carrinho, quantidade=2,
        produto_id=contexto_carrinho["produto_2_id"],
    )
    assert resposta.status_code == 200, resposta.text
    assert len(resposta.json()["itens"]) == 2
    assert resposta.json()["quantidade_itens"] == 4
    assert Decimal(str(resposta.json()["valor_total"])) == Decimal("151.00")


def test_atualizar_quantidade(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho).status_code == 200
    resposta = client.patch(
        f"/carrinho/itens/{contexto_carrinho['produto_id']}",
        json={"quantidade": 4},
        headers=contexto_carrinho["headers_1"],
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["quantidade_itens"] == 4
    assert Decimal(str(resposta.json()["valor_total"])) == Decimal("200.00")


def test_remover_produto(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho).status_code == 200
    resposta = client.delete(
        f"/carrinho/itens/{contexto_carrinho['produto_id']}",
        headers=contexto_carrinho["headers_1"],
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["itens"] == []


def test_esvaziar_carrinho(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho).status_code == 200
    resposta = client.delete("/carrinho", headers=contexto_carrinho["headers_1"])
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["itens"] == []
    assert resposta.json()["quantidade_itens"] == 0


def test_carrinhos_isolados_por_cliente(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho, quantidade=2).status_code == 200
    resposta = client.get("/carrinho", headers=contexto_carrinho["headers_2"])
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["cliente_id"] == contexto_carrinho["cliente_2"]["id"]
    assert resposta.json()["itens"] == []


def test_cliente_nao_remove_item_de_outro_cliente(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho).status_code == 200
    resposta = client.delete(
        f"/carrinho/itens/{contexto_carrinho['produto_id']}",
        headers=contexto_carrinho["headers_2"],
    )
    assert resposta.status_code == 404
    proprio = client.get("/carrinho", headers=contexto_carrinho["headers_1"])
    assert len(proprio.json()["itens"]) == 1


def test_produto_inexistente(client, contexto_carrinho):
    resposta = adicionar(client, contexto_carrinho, produto_id=999999)
    assert resposta.status_code == 404


def test_estoque_insuficiente(client, contexto_carrinho):
    resposta = adicionar(client, contexto_carrinho, quantidade=11)
    assert resposta.status_code == 409


def test_estoque_insuficiente_ao_somar(client, contexto_carrinho):
    assert adicionar(client, contexto_carrinho, quantidade=8).status_code == 200
    resposta = adicionar(client, contexto_carrinho, quantidade=3)
    assert resposta.status_code == 409
    consulta = client.get("/carrinho", headers=contexto_carrinho["headers_1"])
    assert consulta.json()["quantidade_itens"] == 8


def test_quantidade_zero_rejeitada(client, contexto_carrinho):
    resposta = adicionar(client, contexto_carrinho, quantidade=0)
    assert resposta.status_code == 422


def test_quantidade_negativa_rejeitada(client, contexto_carrinho):
    resposta = adicionar(client, contexto_carrinho, quantidade=-1)
    assert resposta.status_code == 422


def test_atualizar_item_inexistente(client, contexto_carrinho):
    resposta = client.patch(
        f"/carrinho/itens/{contexto_carrinho['produto_id']}",
        json={"quantidade": 2},
        headers=contexto_carrinho["headers_1"],
    )
    assert resposta.status_code == 404


def test_remover_item_inexistente(client, contexto_carrinho):
    resposta = client.delete(
        f"/carrinho/itens/{contexto_carrinho['produto_id']}",
        headers=contexto_carrinho["headers_1"],
    )
    assert resposta.status_code == 404


def test_adicionar_nao_reduz_estoque(client, contexto_carrinho, test_engine):
    assert adicionar(client, contexto_carrinho, quantidade=3).status_code == 200
    with test_engine.connect() as conexao:
        estoque = conexao.execute(
            text("SELECT estoque FROM produtos WHERE id = :id"),
            {"id": contexto_carrinho["produto_id"]},
        ).scalar_one()
    assert estoque == 10


def test_preco_atualizado_reflete_no_carrinho(client, contexto_carrinho, test_engine):
    assert adicionar(client, contexto_carrinho, quantidade=2).status_code == 200
    with test_engine.begin() as conexao:
        conexao.execute(
            text("UPDATE produtos SET preco = 60.00 WHERE id = :id"),
            {"id": contexto_carrinho["produto_id"]},
        )
    resposta = client.get("/carrinho", headers=contexto_carrinho["headers_1"])
    assert resposta.status_code == 200, resposta.text
    assert Decimal(str(resposta.json()["valor_total"])) == Decimal("120.00")

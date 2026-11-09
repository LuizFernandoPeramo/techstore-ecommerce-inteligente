
from decimal import Decimal

import pytest
from sqlalchemy import text


SENHA = "TechStore@2026"


def criar_cliente(client, numero):
    resposta = client.post(
        "/clientes",
        json={
            "nome": f"Cliente Checkout {numero}",
            "email": f"checkout{numero}@exemplo.com",
            "telefone": "11999998888",
            "cpf": f"{numero:011d}",
            "senha": SENHA,
        },
    )

    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autenticar(client, email):
    resposta = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": SENHA,
        },
    )

    assert resposta.status_code == 200, resposta.text

    return {
        "Authorization": (
            f"Bearer {resposta.json()['access_token']}"
        )
    }


def criar_produto(test_engine, nome, preco, estoque):
    with test_engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                INSERT INTO produtos (
                    nome,
                    categoria,
                    preco,
                    estoque
                )
                VALUES (
                    :nome,
                    'Eletronicos',
                    :preco,
                    :estoque
                )
                RETURNING id
            """),
            {
                "nome": nome,
                "preco": Decimal(preco),
                "estoque": estoque,
            },
        )

        return resultado.scalar_one()


def consultar_estoque(test_engine, produto_id):
    with test_engine.connect() as conexao:
        return conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id},
        ).scalar_one()


def contar_registros(test_engine, tabela):
    tabelas_permitidas = {
        "pedidos",
        "itens_pedido",
        "itens_carrinho",
    }

    assert tabela in tabelas_permitidas

    with test_engine.connect() as conexao:
        return conexao.execute(
            text(f"SELECT COUNT(*) FROM {tabela}")
        ).scalar_one()


def adicionar_ao_carrinho(
    client,
    headers,
    produto_id,
    quantidade,
):
    resposta = client.post(
        "/carrinho/itens",
        headers=headers,
        json={
            "produto_id": produto_id,
            "quantidade": quantidade,
        },
    )

    assert resposta.status_code == 200, resposta.text
    return resposta.json()


@pytest.fixture
def contexto_checkout(client, banco_limpo, test_engine):
    cliente = criar_cliente(client, 1001)
    headers = autenticar(client, cliente["email"])

    produto_1 = criar_produto(
        test_engine,
        "Notebook Checkout",
        "2500.00",
        10,
    )

    produto_2 = criar_produto(
        test_engine,
        "Mouse Checkout",
        "80.00",
        20,
    )

    return {
        "client": client,
        "engine": test_engine,
        "cliente": cliente,
        "headers": headers,
        "produto_1": produto_1,
        "produto_2": produto_2,
    }


def test_checkout_exige_autenticacao(client, banco_limpo):
    resposta = client.post("/carrinho/checkout")

    assert resposta.status_code == 401


def test_checkout_rejeita_token_invalido(client, banco_limpo):
    resposta = client.post(
        "/carrinho/checkout",
        headers={
            "Authorization": "Bearer token-invalido"
        },
    )

    assert resposta.status_code == 401


def test_checkout_rejeita_carrinho_inexistente(
    contexto_checkout,
):
    dados = contexto_checkout

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 409
    assert contar_registros(dados["engine"], "pedidos") == 0


def test_checkout_rejeita_carrinho_vazio(
    contexto_checkout,
):
    dados = contexto_checkout

    consulta = dados["client"].get(
        "/carrinho",
        headers=dados["headers"],
    )

    assert consulta.status_code == 200

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 409
    assert contar_registros(dados["engine"], "pedidos") == 0


def test_checkout_cria_pedido_com_um_produto(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        2,
    )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text

    pedido = resposta.json()

    assert pedido["cliente_id"] == dados["cliente"]["id"]
    assert pedido["status"] == "pendente"
    assert Decimal(str(pedido["valor_total"])) == Decimal(
        "5000.00"
    )
    assert len(pedido["itens"]) == 1

    item = pedido["itens"][0]

    assert item["produto_id"] == dados["produto_1"]
    assert item["quantidade"] == 2
    assert Decimal(str(item["preco_unitario"])) == Decimal(
        "2500.00"
    )
    assert Decimal(str(item["subtotal"])) == Decimal(
        "5000.00"
    )


def test_checkout_cria_pedido_com_multiplos_produtos(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        1,
    )

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_2"],
        3,
    )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text

    pedido = resposta.json()

    assert len(pedido["itens"]) == 2
    assert Decimal(str(pedido["valor_total"])) == Decimal(
        "2740.00"
    )
    assert contar_registros(
        dados["engine"],
        "itens_pedido",
    ) == 2


def test_checkout_desconta_estoque(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        3,
    )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text

    assert consultar_estoque(
        dados["engine"],
        dados["produto_1"],
    ) == 7


def test_checkout_esvazia_carrinho(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        1,
    )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text

    carrinho = dados["client"].get(
        "/carrinho",
        headers=dados["headers"],
    )

    assert carrinho.status_code == 200

    dados_carrinho = carrinho.json()

    assert dados_carrinho["itens"] == []
    assert dados_carrinho["quantidade_itens"] == 0
    assert Decimal(
        str(dados_carrinho["valor_total"])
    ) == Decimal("0.00")


def test_checkout_nao_desconta_estoque_ao_adicionar(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        4,
    )

    assert consultar_estoque(
        dados["engine"],
        dados["produto_1"],
    ) == 10

    assert contar_registros(
        dados["engine"],
        "pedidos",
    ) == 0


def test_checkout_rejeita_estoque_insuficiente(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        5,
    )

    with dados["engine"].begin() as conexao:
        conexao.execute(
            text("""
                UPDATE produtos
                SET estoque = 2
                WHERE id = :produto_id
            """),
            {"produto_id": dados["produto_1"]},
        )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 409

    assert contar_registros(
        dados["engine"],
        "pedidos",
    ) == 0

    assert consultar_estoque(
        dados["engine"],
        dados["produto_1"],
    ) == 2

    carrinho = dados["client"].get(
        "/carrinho",
        headers=dados["headers"],
    )

    assert carrinho.status_code == 200
    assert carrinho.json()["quantidade_itens"] == 5


def test_checkout_preserva_todos_itens_em_falha(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        2,
    )

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_2"],
        5,
    )

    with dados["engine"].begin() as conexao:
        conexao.execute(
            text("""
                UPDATE produtos
                SET estoque = 1
                WHERE id = :produto_id
            """),
            {"produto_id": dados["produto_2"]},
        )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 409

    assert contar_registros(
        dados["engine"],
        "pedidos",
    ) == 0

    assert contar_registros(
        dados["engine"],
        "itens_pedido",
    ) == 0

    assert consultar_estoque(
        dados["engine"],
        dados["produto_1"],
    ) == 10

    assert consultar_estoque(
        dados["engine"],
        dados["produto_2"],
    ) == 1

    carrinho = dados["client"].get(
        "/carrinho",
        headers=dados["headers"],
    )

    assert carrinho.status_code == 200
    assert len(carrinho.json()["itens"]) == 2
    assert carrinho.json()["quantidade_itens"] == 7


def test_checkout_rejeita_produto_inativo(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        1,
    )

    with dados["engine"].begin() as conexao:
        conexao.execute(
            text("""
                UPDATE produtos
                SET ativo = FALSE
                WHERE id = :produto_id
            """),
            {"produto_id": dados["produto_1"]},
        )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 404
    assert contar_registros(dados["engine"], "pedidos") == 0
    assert contar_registros(
        dados["engine"],
        "itens_carrinho",
    ) == 1


def test_checkout_utiliza_preco_atual(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        2,
    )

    with dados["engine"].begin() as conexao:
        conexao.execute(
            text("""
                UPDATE produtos
                SET preco = 2700.00
                WHERE id = :produto_id
            """),
            {"produto_id": dados["produto_1"]},
        )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text

    pedido = resposta.json()

    assert Decimal(str(pedido["valor_total"])) == Decimal(
        "5400.00"
    )

    assert Decimal(
        str(pedido["itens"][0]["preco_unitario"])
    ) == Decimal("2700.00")


def test_checkout_nao_duplica_pedido(
    contexto_checkout,
):
    dados = contexto_checkout

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        1,
    )

    primeira_resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    segunda_resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert primeira_resposta.status_code == 201
    assert segunda_resposta.status_code == 409

    assert contar_registros(
        dados["engine"],
        "pedidos",
    ) == 1

    assert consultar_estoque(
        dados["engine"],
        dados["produto_1"],
    ) == 9


def test_checkout_respeita_isolamento_entre_clientes(
    contexto_checkout,
):
    dados = contexto_checkout

    segundo_cliente = criar_cliente(
        dados["client"],
        1002,
    )

    segundo_headers = autenticar(
        dados["client"],
        segundo_cliente["email"],
    )

    adicionar_ao_carrinho(
        dados["client"],
        dados["headers"],
        dados["produto_1"],
        2,
    )

    adicionar_ao_carrinho(
        dados["client"],
        segundo_headers,
        dados["produto_2"],
        3,
    )

    resposta = dados["client"].post(
        "/carrinho/checkout",
        headers=dados["headers"],
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["cliente_id"] == dados["cliente"]["id"]

    outro_carrinho = dados["client"].get(
        "/carrinho",
        headers=segundo_headers,
    )

    assert outro_carrinho.status_code == 200
    assert outro_carrinho.json()["quantidade_itens"] == 3
    assert len(outro_carrinho.json()["itens"]) == 1

    assert consultar_estoque(
        dados["engine"],
        dados["produto_2"],
    ) == 20

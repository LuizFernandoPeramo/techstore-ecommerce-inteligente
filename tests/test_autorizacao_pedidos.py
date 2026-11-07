import pytest
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


def criar_cliente(client, numero):
    resposta = client.post(
        "/clientes",
        json={
            "nome": f"Cliente Pedido {numero}",
            "email": f"pedido{numero}@exemplo.com",
            "telefone": "11999998888",
            "cpf": f"{numero:011d}",
            "senha": SENHA_TESTE,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autenticar(client, cliente):
    resposta = client.post(
        "/auth/login",
        json={"email": cliente["email"], "senha": SENHA_TESTE},
    )
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def promover_administrador(test_engine, cliente_id):
    with test_engine.begin() as conexao:
        banco = conexao.execute(text("SELECT current_database() ")).scalar_one()
        if banco != "techstore_test_db":
            raise RuntimeError("Banco de testes incorreto")
        resultado = conexao.execute(
            text("UPDATE clientes SET perfil = 'admin' WHERE id = :id RETURNING id"),
            {"id": cliente_id},
        )
        assert resultado.scalar_one() == cliente_id


@pytest.fixture
def contexto_pedidos(client, test_engine, banco_limpo):
    cliente_1 = criar_cliente(client, 101)
    cliente_2 = criar_cliente(client, 102)
    administrador = criar_cliente(client, 103)
    promover_administrador(test_engine, administrador["id"])

    headers_cliente_1 = autenticar(client, cliente_1)
    headers_cliente_2 = autenticar(client, cliente_2)
    headers_admin = autenticar(client, administrador)

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Produto de Teste de Autorizacao",
            "categoria": "Perifericos",
            "preco": "50.00",
            "estoque": 30,
        },
        headers=headers_admin,
    )
    assert resposta_produto.status_code == 201, resposta_produto.text

    return {
        "clientes": (cliente_1, cliente_2),
        "headers": (headers_cliente_1, headers_cliente_2),
        "admin": administrador,
        "headers_admin": headers_admin,
        "produto_id": resposta_produto.json()["id"],
    }


def dados_pedido(cliente_id, produto_id):
    return {
        "cliente_id": cliente_id,
        "itens": [{"produto_id": produto_id, "quantidade": 1}],
    }


def criar_pedido(client, contexto, indice_cliente=0, como_admin=False):
    cliente = contexto["clientes"][indice_cliente]
    headers = (
        contexto["headers_admin"]
        if como_admin
        else contexto["headers"][indice_cliente]
    )
    resposta = client.post(
        "/pedidos",
        json=dados_pedido(cliente["id"], contexto["produto_id"]),
        headers=headers,
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.mark.parametrize("metodo", ["post", "get_lista", "get_detalhe", "patch"])
def test_pedidos_sem_token(client, contexto_pedidos, metodo):
    contexto = contexto_pedidos
    if metodo == "post":
        resposta = client.post(
            "/pedidos",
            json=dados_pedido(contexto["clientes"][0]["id"], contexto["produto_id"]),
        )
    elif metodo == "get_lista":
        resposta = client.get("/pedidos")
    elif metodo == "get_detalhe":
        resposta = client.get("/pedidos/1")
    else:
        resposta = client.patch("/pedidos/1/status", json={"status": "pago"})
    assert resposta.status_code == 401


@pytest.mark.parametrize("metodo", ["post", "get_lista", "get_detalhe", "patch"])
def test_pedidos_token_invalido(client, contexto_pedidos, metodo):
    contexto = contexto_pedidos
    headers = {"Authorization": "Bearer token-invalido"}
    if metodo == "post":
        resposta = client.post(
            "/pedidos",
            json=dados_pedido(contexto["clientes"][0]["id"], contexto["produto_id"]),
            headers=headers,
        )
    elif metodo == "get_lista":
        resposta = client.get("/pedidos", headers=headers)
    elif metodo == "get_detalhe":
        resposta = client.get("/pedidos/1", headers=headers)
    else:
        resposta = client.patch(
            "/pedidos/1/status", json={"status": "pago"}, headers=headers
        )
    assert resposta.status_code == 401


def test_cliente_cria_pedido_proprio(client, contexto_pedidos):
    pedido = criar_pedido(client, contexto_pedidos)
    assert pedido["cliente_id"] == contexto_pedidos["clientes"][0]["id"]


def test_cliente_nao_cria_pedido_para_terceiro(client, contexto_pedidos):
    contexto = contexto_pedidos
    resposta = client.post(
        "/pedidos",
        json=dados_pedido(contexto["clientes"][1]["id"], contexto["produto_id"]),
        headers=contexto["headers"][0],
    )
    assert resposta.status_code == 403


def test_cliente_lista_somente_pedidos_proprios(client, contexto_pedidos):
    contexto = contexto_pedidos
    proprio = criar_pedido(client, contexto, 0)
    outro = criar_pedido(client, contexto, 1)
    resposta = client.get("/pedidos", headers=contexto["headers"][0])
    assert resposta.status_code == 200, resposta.text
    pedidos = resposta.json()
    assert isinstance(pedidos, list)
    ids = {pedido["id"] for pedido in pedidos}
    assert proprio["id"] in ids
    assert outro["id"] not in ids
    assert all(pedido["cliente_id"] == contexto["clientes"][0]["id"] for pedido in pedidos)


def test_cliente_consulta_pedido_proprio(client, contexto_pedidos):
    contexto = contexto_pedidos
    pedido = criar_pedido(client, contexto)
    resposta = client.get(f"/pedidos/{pedido['id']}", headers=contexto["headers"][0])
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["id"] == pedido["id"]


def test_cliente_nao_consulta_pedido_de_terceiro(client, contexto_pedidos):
    contexto = contexto_pedidos
    pedido = criar_pedido(client, contexto, 1)
    resposta = client.get(f"/pedidos/{pedido['id']}", headers=contexto["headers"][0])
    assert resposta.status_code == 403


def test_cliente_nao_altera_status(client, contexto_pedidos):
    contexto = contexto_pedidos
    pedido = criar_pedido(client, contexto)
    resposta = client.patch(
        f"/pedidos/{pedido['id']}/status",
        json={"status": "pago"},
        headers=contexto["headers"][0],
    )
    assert resposta.status_code == 403


def test_administrador_cria_pedido_para_outro_cliente(client, contexto_pedidos):
    pedido = criar_pedido(client, contexto_pedidos, 1, como_admin=True)
    assert pedido["cliente_id"] == contexto_pedidos["clientes"][1]["id"]


def test_administrador_lista_todos_os_pedidos(client, contexto_pedidos):
    contexto = contexto_pedidos
    primeiro = criar_pedido(client, contexto, 0)
    segundo = criar_pedido(client, contexto, 1)
    resposta = client.get("/pedidos", headers=contexto["headers_admin"])
    assert resposta.status_code == 200, resposta.text
    ids = {pedido["id"] for pedido in resposta.json()}
    assert {primeiro["id"], segundo["id"]}.issubset(ids)


def test_administrador_consulta_pedido_de_cliente(client, contexto_pedidos):
    contexto = contexto_pedidos
    pedido = criar_pedido(client, contexto, 1)
    resposta = client.get(f"/pedidos/{pedido['id']}", headers=contexto["headers_admin"])
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["id"] == pedido["id"]


def test_administrador_altera_status_pedido(client, contexto_pedidos):
    contexto = contexto_pedidos
    pedido = criar_pedido(client, contexto)
    resposta = client.patch(
        f"/pedidos/{pedido['id']}/status",
        json={"status": "pago"},
        headers=contexto["headers_admin"],
    )
    assert resposta.status_code == 200, resposta.text
    consulta = client.get(f"/pedidos/{pedido['id']}", headers=contexto["headers_admin"])
    assert consulta.status_code == 200, consulta.text
    assert consulta.json()["status"] == "pago"

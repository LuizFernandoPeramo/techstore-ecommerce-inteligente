
from decimal import Decimal

import pytest
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


def criar_usuario(client, numero):
    dados = {
        "nome": f"Usuario Teste {numero}",
        "email": f"usuario.produto{numero}@exemplo.com",
        "telefone": "11999998888",
        "cpf": f"{numero:011d}",
        "senha": SENHA_TESTE
    }

    resposta = client.post("/clientes", json=dados)

    assert resposta.status_code == 201, resposta.text

    return resposta.json()


def obter_headers(client, email):
    resposta = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": SENHA_TESTE
        }
    )

    assert resposta.status_code == 200, resposta.text

    token = resposta.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def criar_administrador(client, test_engine):
    usuario = criar_usuario(client, 1)

    with test_engine.begin() as conexao:
        banco = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco != "techstore_test_db":
            raise RuntimeError("Banco de testes incorreto")

        resultado = conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'admin'
                WHERE id = :cliente_id
                  AND perfil = 'cliente'
                RETURNING id
            """),
            {"cliente_id": usuario["id"]}
        )

        assert resultado.scalar_one() == usuario["id"]

    return usuario, obter_headers(client, usuario["email"])


def cadastrar_produto_admin(client, headers, dados):
    resposta = client.post(
        "/produtos",
        json=dados,
        headers=headers
    )

    assert resposta.status_code == 201, resposta.text

    return resposta.json()


def test_cadastrar_produto(client, test_engine, banco_limpo):
    _, headers = criar_administrador(client, test_engine)

    novo_produto = {
        "nome": "Monitor LG UltraWide",
        "categoria": "Monitores",
        "preco": 1299.90,
        "estoque": 15
    }

    resposta = client.post(
        "/produtos",
        json=novo_produto,
        headers=headers
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Monitor LG UltraWide"
    assert dados["categoria"] == "Monitores"
    assert Decimal(str(dados["preco"])) == Decimal("1299.90")
    assert dados["estoque"] == 15

    produto_id = dados["id"]

    with test_engine.connect() as conexao:
        produto_banco = conexao.execute(
            text("""
                SELECT id, nome, categoria, preco, estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).mappings().first()

    assert produto_banco is not None
    assert produto_banco["nome"] == "Monitor LG UltraWide"
    assert produto_banco["categoria"] == "Monitores"
    assert produto_banco["preco"] == Decimal("1299.90")
    assert produto_banco["estoque"] == 15


def test_consultar_produto(client, test_engine, banco_limpo):
    _, headers = criar_administrador(client, test_engine)

    novo_produto = {
        "nome": "Teclado Logitech K120",
        "categoria": "Acessorios",
        "preco": 89.90,
        "estoque": 25
    }

    produto = cadastrar_produto_admin(
        client,
        headers,
        novo_produto
    )

    resposta = client.get(f"/produtos/{produto['id']}")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["id"] == produto["id"]
    assert dados["nome"] == "Teclado Logitech K120"
    assert dados["categoria"] == "Acessorios"
    assert Decimal(str(dados["preco"])) == Decimal("89.90")
    assert dados["estoque"] == 25


def test_atualizar_produto(client, test_engine, banco_limpo):
    _, headers = criar_administrador(client, test_engine)

    novo_produto = {
        "nome": "Mouse Gamer",
        "categoria": "Acessorios",
        "preco": 150.00,
        "estoque": 20
    }

    produto = cadastrar_produto_admin(
        client,
        headers,
        novo_produto
    )

    produto_atualizado = {
        "nome": "Mouse Gamer Logitech G203",
        "categoria": "Acessorios",
        "preco": 179.90,
        "estoque": 35
    }

    resposta = client.put(
        f"/produtos/{produto['id']}",
        json=produto_atualizado,
        headers=headers
    )

    assert resposta.status_code == 200

    resposta_consulta = client.get(
        f"/produtos/{produto['id']}"
    )

    assert resposta_consulta.status_code == 200

    dados = resposta_consulta.json()

    assert dados["nome"] == "Mouse Gamer Logitech G203"
    assert dados["categoria"] == "Acessorios"
    assert Decimal(str(dados["preco"])) == Decimal("179.90")
    assert dados["estoque"] == 35

    with test_engine.connect() as conexao:
        produto_banco = conexao.execute(
            text("""
                SELECT nome, categoria, preco, estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto["id"]}
        ).mappings().first()

    assert produto_banco is not None
    assert produto_banco["nome"] == "Mouse Gamer Logitech G203"
    assert produto_banco["categoria"] == "Acessorios"
    assert produto_banco["preco"] == Decimal("179.90")
    assert produto_banco["estoque"] == 35


def test_exclusao_logica_produto(
    client,
    test_engine,
    banco_limpo
):
    _, headers = criar_administrador(client, test_engine)

    novo_produto = {
        "nome": "Webcam Logitech C920",
        "categoria": "Acessorios",
        "preco": 399.90,
        "estoque": 10
    }

    produto = cadastrar_produto_admin(
        client,
        headers,
        novo_produto
    )

    produto_id = produto["id"]

    resposta = client.delete(
        f"/produtos/{produto_id}",
        headers=headers
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["mensagem"] == "Produto desativado com sucesso"
    assert dados["id"] == produto_id
    assert dados["nome"] == "Webcam Logitech C920"

    with test_engine.connect() as conexao:
        produto_banco = conexao.execute(
            text("""
                SELECT id, nome, ativo
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).mappings().first()

    assert produto_banco is not None
    assert produto_banco["ativo"] is False

    resposta_consulta = client.get(
        f"/produtos/{produto_id}"
    )

    assert resposta_consulta.status_code == 404

    resposta_listagem = client.get("/produtos")

    assert resposta_listagem.status_code == 200
    assert all(
        item["id"] != produto_id
        for item in resposta_listagem.json()
    )

    resposta_segunda_exclusao = client.delete(
        f"/produtos/{produto_id}",
        headers=headers
    )

    assert resposta_segunda_exclusao.status_code == 404


def test_listagem_publica_produtos(
    client,
    test_engine,
    banco_limpo
):
    _, headers = criar_administrador(client, test_engine)

    cadastrar_produto_admin(
        client,
        headers,
        {
            "nome": "Notebook Teste",
            "categoria": "Notebooks",
            "preco": 3500.00,
            "estoque": 5
        }
    )

    resposta = client.get("/produtos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


@pytest.mark.parametrize(
    "metodo",
    ["post", "put", "delete"]
)
def test_operacao_administrativa_sem_token(
    client,
    test_engine,
    banco_limpo,
    metodo
):
    dados = {
        "nome": "Produto Protegido",
        "categoria": "Testes",
        "preco": 100.00,
        "estoque": 10
    }

    if metodo == "post":
        resposta = client.post("/produtos", json=dados)
    else:
        _, headers = criar_administrador(client, test_engine)
        produto = cadastrar_produto_admin(client, headers, dados)

        if metodo == "put":
            resposta = client.put(
                f"/produtos/{produto['id']}",
                json=dados
            )
        else:
            resposta = client.delete(
                f"/produtos/{produto['id']}"
            )

    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "metodo",
    ["post", "put", "delete"]
)
def test_cliente_nao_pode_administrar_produtos(
    client,
    test_engine,
    banco_limpo,
    metodo
):
    cliente_comum = criar_usuario(client, 2)
    headers_cliente = obter_headers(
        client,
        cliente_comum["email"]
    )

    dados = {
        "nome": "Produto Restrito",
        "categoria": "Testes",
        "preco": 250.00,
        "estoque": 8
    }

    if metodo == "post":
        resposta = client.post(
            "/produtos",
            json=dados,
            headers=headers_cliente
        )
    else:
        _, headers_admin = criar_administrador(
            client,
            test_engine
        )

        produto = cadastrar_produto_admin(
            client,
            headers_admin,
            dados
        )

        if metodo == "put":
            resposta = client.put(
                f"/produtos/{produto['id']}",
                json=dados,
                headers=headers_cliente
            )
        else:
            resposta = client.delete(
                f"/produtos/{produto['id']}",
                headers=headers_cliente
            )

    assert resposta.status_code == 403


@pytest.mark.parametrize(
    "metodo",
    ["post", "put", "delete"]
)
def test_operacao_administrativa_token_invalido(
    client,
    test_engine,
    banco_limpo,
    metodo
):
    dados = {
        "nome": "Produto Token Invalido",
        "categoria": "Testes",
        "preco": 90.00,
        "estoque": 3
    }

    headers_invalidos = {
        "Authorization": "Bearer token-invalido"
    }

    if metodo == "post":
        resposta = client.post(
            "/produtos",
            json=dados,
            headers=headers_invalidos
        )
    else:
        _, headers_admin = criar_administrador(
            client,
            test_engine
        )

        produto = cadastrar_produto_admin(
            client,
            headers_admin,
            dados
        )

        if metodo == "put":
            resposta = client.put(
                f"/produtos/{produto['id']}",
                json=dados,
                headers=headers_invalidos
            )
        else:
            resposta = client.delete(
                f"/produtos/{produto['id']}",
                headers=headers_invalidos
            )

    assert resposta.status_code == 401


def test_administrador_rebaixado_perde_acesso_produtos(
    client,
    test_engine,
    banco_limpo
):
    administrador, headers = criar_administrador(
        client,
        test_engine
    )

    dados = {
        "nome": "Produto Antes do Rebaixamento",
        "categoria": "Testes",
        "preco": 100.00,
        "estoque": 5
    }

    resposta_inicial = client.post(
        "/produtos",
        json=dados,
        headers=headers
    )

    assert resposta_inicial.status_code == 201

    with test_engine.begin() as conexao:
        conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'cliente'
                WHERE id = :cliente_id
            """),
            {"cliente_id": administrador["id"]}
        )

    resposta_final = client.post(
        "/produtos",
        json=dados,
        headers=headers
    )

    assert resposta_final.status_code == 403

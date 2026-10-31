
from decimal import Decimal

from sqlalchemy import text


def test_cadastrar_produto(client, test_engine, banco_limpo):
    novo_produto = {
        "nome": "Monitor LG UltraWide",
        "categoria": "Monitores",
        "preco": 1299.90,
        "estoque": 15
    }

    resposta = client.post(
        "/produtos",
        json=novo_produto
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Monitor LG UltraWide"
    assert dados["categoria"] == "Monitores"
    assert Decimal(str(dados["preco"])) == Decimal("1299.90")
    assert dados["estoque"] == 15

    produto_id = dados["id"]

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id, nome, categoria, preco, estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        )

        produto_banco = resultado.mappings().first()

    assert produto_banco is not None
    assert produto_banco["nome"] == "Monitor LG UltraWide"
    assert produto_banco["categoria"] == "Monitores"
    assert produto_banco["preco"] == Decimal("1299.90")
    assert produto_banco["estoque"] == 15


def test_consultar_produto(client, banco_limpo):
    novo_produto = {
        "nome": "Teclado Logitech K120",
        "categoria": "Acessorios",
        "preco": 89.90,
        "estoque": 25
    }

    resposta_cadastro = client.post(
        "/produtos",
        json=novo_produto
    )

    assert resposta_cadastro.status_code == 201

    produto_id = resposta_cadastro.json()["id"]

    resposta_consulta = client.get(
        f"/produtos/{produto_id}"
    )

    assert resposta_consulta.status_code == 200

    dados = resposta_consulta.json()

    assert dados["id"] == produto_id
    assert dados["nome"] == "Teclado Logitech K120"
    assert dados["categoria"] == "Acessorios"
    assert Decimal(str(dados["preco"])) == Decimal("89.90")
    assert dados["estoque"] == 25


def test_atualizar_produto(client, test_engine, banco_limpo):
    novo_produto = {
        "nome": "Mouse Gamer",
        "categoria": "Acessorios",
        "preco": 150.00,
        "estoque": 20
    }

    resposta_cadastro = client.post(
        "/produtos",
        json=novo_produto
    )

    assert resposta_cadastro.status_code == 201

    produto_id = resposta_cadastro.json()["id"]

    produto_atualizado = {
        "nome": "Mouse Gamer Logitech G203",
        "categoria": "Acessorios",
        "preco": 179.90,
        "estoque": 35
    }

    resposta_atualizacao = client.put(
        f"/produtos/{produto_id}",
        json=produto_atualizado
    )

    assert resposta_atualizacao.status_code == 200

    resposta_consulta = client.get(
        f"/produtos/{produto_id}"
    )

    assert resposta_consulta.status_code == 200

    dados = resposta_consulta.json()

    assert dados["nome"] == "Mouse Gamer Logitech G203"
    assert dados["categoria"] == "Acessorios"
    assert Decimal(str(dados["preco"])) == Decimal("179.90")
    assert dados["estoque"] == 35

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT nome, categoria, preco, estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        )

        produto_banco = resultado.mappings().first()

    assert produto_banco is not None
    assert produto_banco["nome"] == "Mouse Gamer Logitech G203"
    assert produto_banco["categoria"] == "Acessorios"
    assert produto_banco["preco"] == Decimal("179.90")
    assert produto_banco["estoque"] == 35


def test_exclusao_logica_produto(client, test_engine, banco_limpo):
    novo_produto = {
        "nome": "Webcam Logitech C920",
        "categoria": "Acessorios",
        "preco": 399.90,
        "estoque": 10
    }

    resposta_cadastro = client.post(
        "/produtos",
        json=novo_produto
    )

    assert resposta_cadastro.status_code == 201

    produto_id = resposta_cadastro.json()["id"]

    resposta_exclusao = client.delete(
        f"/produtos/{produto_id}"
    )

    assert resposta_exclusao.status_code == 200

    dados_exclusao = resposta_exclusao.json()

    assert dados_exclusao["mensagem"] == "Produto desativado com sucesso"
    assert dados_exclusao["id"] == produto_id
    assert dados_exclusao["nome"] == "Webcam Logitech C920"

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id, nome, ativo
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        )

        produto_banco = resultado.mappings().first()

    assert produto_banco is not None
    assert produto_banco["ativo"] is False

    resposta_consulta = client.get(
        f"/produtos/{produto_id}"
    )

    assert resposta_consulta.status_code == 404

    resposta_listagem = client.get("/produtos")

    assert resposta_listagem.status_code == 200
    assert all(
        produto["id"] != produto_id
        for produto in resposta_listagem.json()
    )

    resposta_segunda_exclusao = client.delete(
        f"/produtos/{produto_id}"
    )

    assert resposta_segunda_exclusao.status_code == 404

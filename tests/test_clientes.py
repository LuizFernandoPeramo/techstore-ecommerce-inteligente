
from sqlalchemy import text


def test_cadastrar_cliente(client, test_engine, banco_limpo):
    novo_cliente = {
        "nome": "Mariana Oliveira",
        "email": "mariana.oliveira@exemplo.com",
        "telefone": "11987654321",
        "cpf": "12345678901"
    }

    resposta = client.post("/clientes", json=novo_cliente)

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["id"] > 0
    assert dados["nome"] == "Mariana Oliveira"
    assert dados["email"] == "mariana.oliveira@exemplo.com"
    assert dados["telefone"] == "11987654321"
    assert dados["cpf"] == "12345678901"
    assert dados["ativo"] is True

    cliente_id = dados["id"]

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id, nome, email, telefone, cpf, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        )

        cliente_banco = resultado.mappings().first()

    assert cliente_banco is not None
    assert cliente_banco["id"] == cliente_id
    assert cliente_banco["nome"] == "Mariana Oliveira"
    assert cliente_banco["email"] == "mariana.oliveira@exemplo.com"
    assert cliente_banco["telefone"] == "11987654321"
    assert cliente_banco["cpf"] == "12345678901"
    assert cliente_banco["ativo"] is True


def test_consultar_cliente(client, banco_limpo):
    novo_cliente = {
        "nome": "Carlos Henrique",
        "email": "carlos.henrique@exemplo.com",
        "telefone": "11999998888",
        "cpf": "98765432100"
    }

    resposta_cadastro = client.post("/clientes", json=novo_cliente)

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    resposta_consulta = client.get(f"/clientes/{cliente_id}")

    assert resposta_consulta.status_code == 200

    dados = resposta_consulta.json()

    assert dados["id"] == cliente_id
    assert dados["nome"] == "Carlos Henrique"
    assert dados["email"] == "carlos.henrique@exemplo.com"
    assert dados["telefone"] == "11999998888"
    assert dados["cpf"] == "98765432100"
    assert dados["ativo"] is True


def test_consultar_cliente_inexistente(client, banco_limpo):
    resposta = client.get("/clientes/99999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Cliente nao encontrado"


def test_atualizar_cliente(client, test_engine, banco_limpo):
    novo_cliente = {
        "nome": "Ana Souza",
        "email": "ana.souza@exemplo.com",
        "telefone": "11988887777",
        "cpf": "11122233344"
    }

    resposta_cadastro = client.post("/clientes", json=novo_cliente)

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    cliente_atualizado = {
        "nome": "Ana Paula Souza",
        "email": "ana.paula@exemplo.com",
        "telefone": "11977776666",
        "cpf": "11122233344"
    }

    resposta_atualizacao = client.put(
        f"/clientes/{cliente_id}",
        json=cliente_atualizado
    )

    assert resposta_atualizacao.status_code == 200

    dados = resposta_atualizacao.json()

    assert dados["id"] == cliente_id
    assert dados["nome"] == "Ana Paula Souza"
    assert dados["email"] == "ana.paula@exemplo.com"
    assert dados["telefone"] == "11977776666"
    assert dados["cpf"] == "11122233344"
    assert dados["ativo"] is True

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id, nome, email, telefone, cpf, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        )

        cliente_banco = resultado.mappings().first()

    assert cliente_banco is not None
    assert cliente_banco["nome"] == "Ana Paula Souza"
    assert cliente_banco["email"] == "ana.paula@exemplo.com"
    assert cliente_banco["telefone"] == "11977776666"
    assert cliente_banco["cpf"] == "11122233344"
    assert cliente_banco["ativo"] is True


def test_exclusao_logica_cliente(client, test_engine, banco_limpo):
    novo_cliente = {
        "nome": "Roberto Almeida",
        "email": "roberto.almeida@exemplo.com",
        "telefone": "11966665555",
        "cpf": "55566677788"
    }

    resposta_cadastro = client.post("/clientes", json=novo_cliente)

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    resposta_exclusao = client.delete(f"/clientes/{cliente_id}")

    assert resposta_exclusao.status_code == 200

    dados = resposta_exclusao.json()

    assert dados["mensagem"] == "Cliente desativado com sucesso"
    assert dados["id"] == cliente_id
    assert dados["nome"] == "Roberto Almeida"

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id, nome, email, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        )

        cliente_banco = resultado.mappings().first()

    assert cliente_banco is not None
    assert cliente_banco["id"] == cliente_id
    assert cliente_banco["nome"] == "Roberto Almeida"
    assert cliente_banco["email"] == "roberto.almeida@exemplo.com"
    assert cliente_banco["ativo"] is False

    resposta_consulta = client.get(f"/clientes/{cliente_id}")

    assert resposta_consulta.status_code == 404

    resposta_nova_exclusao = client.delete(f"/clientes/{cliente_id}")

    assert resposta_nova_exclusao.status_code == 404

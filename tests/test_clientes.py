
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


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
    assert dados["nome"] == novo_cliente["nome"]
    assert dados["email"] == novo_cliente["email"]
    assert dados["telefone"] == novo_cliente["telefone"]
    assert dados["cpf"] == novo_cliente["cpf"]
    assert dados["ativo"] is True

    with test_engine.connect() as conexao:
        cliente_banco = conexao.execute(
            text("""
                SELECT id, nome, email, telefone, cpf, ativo, perfil
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": dados["id"]}
        ).mappings().one()

    assert cliente_banco["nome"] == novo_cliente["nome"]
    assert cliente_banco["email"] == novo_cliente["email"]
    assert cliente_banco["telefone"] == novo_cliente["telefone"]
    assert cliente_banco["cpf"] == novo_cliente["cpf"]
    assert cliente_banco["ativo"] is True
    assert cliente_banco["perfil"] == "cliente"


def test_consultar_cliente(
    client,
    banco_limpo,
    cliente_autenticado
):
    novo_cliente = {
        "nome": "Carlos Henrique",
        "email": "carlos.henrique@exemplo.com",
        "telefone": "11999998888",
        "cpf": "98765432100",
        "senha": SENHA_TESTE
    }

    resposta_cadastro = client.post(
        "/clientes",
        json=novo_cliente
    )

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    headers = cliente_autenticado(
        novo_cliente["email"],
        SENHA_TESTE
    )

    resposta = client.get(
        f"/clientes/{cliente_id}",
        headers=headers
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["id"] == cliente_id
    assert dados["nome"] == novo_cliente["nome"]
    assert dados["email"] == novo_cliente["email"]
    assert dados["telefone"] == novo_cliente["telefone"]
    assert dados["cpf"] == novo_cliente["cpf"]
    assert dados["ativo"] is True


def test_consultar_cliente_inexistente(
    client,
    banco_limpo,
    cliente_autenticado,
    test_engine
):
    novo_cliente = {
        "nome": "Administrador Teste",
        "email": "admin.teste@exemplo.com",
        "senha": SENHA_TESTE
    }

    resposta_cadastro = client.post(
        "/clientes",
        json=novo_cliente
    )

    assert resposta_cadastro.status_code == 201

    admin_id = resposta_cadastro.json()["id"]

    with test_engine.begin() as conexao:
        conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'admin'
                WHERE id = :cliente_id
            """),
            {"cliente_id": admin_id}
        )

    headers = cliente_autenticado(
        novo_cliente["email"],
        SENHA_TESTE
    )

    resposta = client.get(
        "/clientes/99999",
        headers=headers
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Cliente nao encontrado"


def test_atualizar_cliente(
    client,
    test_engine,
    banco_limpo,
    cliente_autenticado
):
    novo_cliente = {
        "nome": "Ana Souza",
        "email": "ana.souza@exemplo.com",
        "telefone": "11988887777",
        "cpf": "11122233344",
        "senha": SENHA_TESTE
    }

    resposta_cadastro = client.post(
        "/clientes",
        json=novo_cliente
    )

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    headers = cliente_autenticado(
        novo_cliente["email"],
        SENHA_TESTE
    )

    cliente_atualizado = {
        "nome": "Ana Paula Souza",
        "email": "ana.paula@exemplo.com",
        "telefone": "11977776666",
        "cpf": "11122233344"
    }

    resposta = client.put(
        f"/clientes/{cliente_id}",
        json=cliente_atualizado,
        headers=headers
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["id"] == cliente_id
    assert dados["nome"] == cliente_atualizado["nome"]
    assert dados["email"] == cliente_atualizado["email"]
    assert dados["telefone"] == cliente_atualizado["telefone"]
    assert dados["cpf"] == cliente_atualizado["cpf"]
    assert dados["ativo"] is True

    with test_engine.connect() as conexao:
        cliente_banco = conexao.execute(
            text("""
                SELECT id, nome, email, telefone, cpf, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).mappings().one()

    assert cliente_banco["nome"] == cliente_atualizado["nome"]
    assert cliente_banco["email"] == cliente_atualizado["email"]
    assert cliente_banco["telefone"] == cliente_atualizado["telefone"]
    assert cliente_banco["cpf"] == cliente_atualizado["cpf"]
    assert cliente_banco["ativo"] is True


def test_exclusao_logica_cliente(
    client,
    test_engine,
    banco_limpo,
    cliente_autenticado
):
    novo_cliente = {
        "nome": "Roberto Almeida",
        "email": "roberto.almeida@exemplo.com",
        "telefone": "11966665555",
        "cpf": "55566677788",
        "senha": SENHA_TESTE
    }

    resposta_cadastro = client.post(
        "/clientes",
        json=novo_cliente
    )

    assert resposta_cadastro.status_code == 201

    cliente_id = resposta_cadastro.json()["id"]

    headers = cliente_autenticado(
        novo_cliente["email"],
        SENHA_TESTE
    )

    resposta_exclusao = client.delete(
        f"/clientes/{cliente_id}",
        headers=headers
    )

    assert resposta_exclusao.status_code == 200

    dados = resposta_exclusao.json()

    assert dados["mensagem"] == "Cliente desativado com sucesso"
    assert dados["id"] == cliente_id
    assert dados["nome"] == novo_cliente["nome"]

    with test_engine.connect() as conexao:
        cliente_banco = conexao.execute(
            text("""
                SELECT id, nome, email, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).mappings().one()

    assert cliente_banco["ativo"] is False

    resposta_consulta = client.get(
        f"/clientes/{cliente_id}",
        headers=headers
    )

    assert resposta_consulta.status_code == 401

    resposta_nova_exclusao = client.delete(
        f"/clientes/{cliente_id}",
        headers=headers
    )

    assert resposta_nova_exclusao.status_code == 401

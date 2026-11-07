
import pytest
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


def criar_cliente(client, numero):
    dados = {
        "nome": f"Cliente Teste {numero}",
        "email": f"cliente{numero}@exemplo.com",
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


def promover_administrador(test_engine, cliente_id):
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
            {"cliente_id": cliente_id}
        )

        assert resultado.scalar_one() == cliente_id


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_operacao_sem_token(client, banco_limpo, metodo):
    cliente = criar_cliente(client, 1)
    url = f"/clientes/{cliente['id']}"

    if metodo == "put":
        resposta = client.put(
            url,
            json={
                "nome": "Cliente Alterado",
                "email": cliente["email"],
                "telefone": "11999998888",
                "cpf": "00000000001"
            }
        )
    else:
        resposta = client.delete(url)

    assert resposta.status_code == 401


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_operacao_com_token_invalido(
    client,
    banco_limpo,
    metodo
):
    cliente = criar_cliente(client, 1)
    url = f"/clientes/{cliente['id']}"

    headers = {"Authorization": "Bearer token-invalido"}

    if metodo == "put":
        resposta = client.put(
            url,
            json={
                "nome": "Cliente Alterado",
                "email": cliente["email"],
                "telefone": "11999998888",
                "cpf": "00000000001"
            },
            headers=headers
        )
    else:
        resposta = client.delete(url, headers=headers)

    assert resposta.status_code == 401


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_cliente_nao_pode_alterar_outra_conta(
    client,
    test_engine,
    banco_limpo,
    metodo
):
    cliente_1 = criar_cliente(client, 1)
    cliente_2 = criar_cliente(client, 2)

    headers = obter_headers(client, cliente_1["email"])
    url = f"/clientes/{cliente_2['id']}"

    if metodo == "put":
        resposta = client.put(
            url,
            json={
                "nome": "Alteracao Indevida",
                "email": cliente_2["email"],
                "telefone": "11999998888",
                "cpf": "00000000002",
                "senha": "SenhaAlterada123"
            },
            headers=headers
        )
    else:
        resposta = client.delete(url, headers=headers)

    assert resposta.status_code == 403

    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT nome, ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_2["id"]}
        ).mappings().one()

    assert resultado["nome"] == cliente_2["nome"]
    assert resultado["ativo"] is True

    resposta_login = client.post(
        "/auth/login",
        json={
            "email": cliente_2["email"],
            "senha": SENHA_TESTE
        }
    )

    assert resposta_login.status_code == 200


def test_cliente_pode_atualizar_propria_conta(
    client,
    banco_limpo
):
    cliente = criar_cliente(client, 1)
    headers = obter_headers(client, cliente["email"])

    resposta = client.put(
        f"/clientes/{cliente['id']}",
        json={
            "nome": "Cliente Atualizado",
            "email": cliente["email"],
            "telefone": "11988887777",
            "cpf": "00000000001"
        },
        headers=headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cliente Atualizado"


def test_cliente_pode_desativar_propria_conta(
    client,
    banco_limpo
):
    cliente = criar_cliente(client, 1)
    headers = obter_headers(client, cliente["email"])

    resposta = client.delete(
        f"/clientes/{cliente['id']}",
        headers=headers
    )

    assert resposta.status_code == 200

    resposta_perfil = client.get(
        "/auth/me",
        headers=headers
    )

    assert resposta_perfil.status_code == 401


def test_cliente_nao_pode_listar_clientes(
    client,
    banco_limpo
):
    cliente = criar_cliente(client, 1)
    headers = obter_headers(client, cliente["email"])

    resposta = client.get("/clientes", headers=headers)

    assert resposta.status_code == 403


def test_administrador_pode_listar_clientes(
    client,
    test_engine,
    banco_limpo
):
    admin = criar_cliente(client, 1)
    criar_cliente(client, 2)

    promover_administrador(test_engine, admin["id"])

    headers = obter_headers(client, admin["email"])

    resposta = client.get("/clientes", headers=headers)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_cliente_pode_consultar_propria_conta(
    client,
    banco_limpo
):
    cliente = criar_cliente(client, 1)
    headers = obter_headers(client, cliente["email"])

    resposta = client.get(
        f"/clientes/{cliente['id']}",
        headers=headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cliente["id"]


def test_cliente_nao_pode_consultar_outra_conta(
    client,
    banco_limpo
):
    cliente_1 = criar_cliente(client, 1)
    cliente_2 = criar_cliente(client, 2)

    headers = obter_headers(client, cliente_1["email"])

    resposta = client.get(
        f"/clientes/{cliente_2['id']}",
        headers=headers
    )

    assert resposta.status_code == 403


def test_administrador_pode_consultar_outra_conta(
    client,
    test_engine,
    banco_limpo
):
    admin = criar_cliente(client, 1)
    cliente = criar_cliente(client, 2)

    promover_administrador(test_engine, admin["id"])
    headers = obter_headers(client, admin["email"])

    resposta = client.get(
        f"/clientes/{cliente['id']}",
        headers=headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cliente["id"]


def test_administrador_pode_atualizar_outra_conta(
    client,
    test_engine,
    banco_limpo
):
    admin = criar_cliente(client, 1)
    cliente = criar_cliente(client, 2)

    promover_administrador(test_engine, admin["id"])
    headers = obter_headers(client, admin["email"])

    resposta = client.put(
        f"/clientes/{cliente['id']}",
        json={
            "nome": "Cliente Atualizado pelo Admin",
            "email": cliente["email"],
            "telefone": "11999998888",
            "cpf": "00000000002"
        },
        headers=headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cliente Atualizado pelo Admin"


def test_administrador_pode_desativar_outra_conta(
    client,
    test_engine,
    banco_limpo
):
    admin = criar_cliente(client, 1)
    cliente = criar_cliente(client, 2)

    promover_administrador(test_engine, admin["id"])
    headers = obter_headers(client, admin["email"])

    resposta = client.delete(
        f"/clientes/{cliente['id']}",
        headers=headers
    )

    assert resposta.status_code == 200

    with test_engine.connect() as conexao:
        ativo = conexao.execute(
            text("""
                SELECT ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente["id"]}
        ).scalar_one()

    assert ativo is False


def test_cadastro_publico_nao_concede_perfil_admin(
    client,
    test_engine,
    banco_limpo
):
    dados = {
        "nome": "Cliente Sem Privilegios",
        "email": "sem.privilegios@exemplo.com",
        "senha": SENHA_TESTE,
        "perfil": "admin"
    }

    resposta = client.post("/clientes", json=dados)

    assert resposta.status_code == 201

    cliente_id = resposta.json()["id"]

    with test_engine.connect() as conexao:
        perfil = conexao.execute(
            text("""
                SELECT perfil
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).scalar_one()

    assert perfil == "cliente"

    headers = obter_headers(client, dados["email"])

    resposta_lista = client.get(
        "/clientes",
        headers=headers
    )

    assert resposta_lista.status_code == 403


def test_administrador_rebaixado_perde_acesso(
    client,
    test_engine,
    banco_limpo
):
    admin = criar_cliente(client, 1)
    promover_administrador(test_engine, admin["id"])

    headers = obter_headers(client, admin["email"])

    resposta_inicial = client.get(
        "/clientes",
        headers=headers
    )

    assert resposta_inicial.status_code == 200

    with test_engine.begin() as conexao:
        conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'cliente'
                WHERE id = :cliente_id
            """),
            {"cliente_id": admin["id"]}
        )

    resposta_final = client.get(
        "/clientes",
        headers=headers
    )

    assert resposta_final.status_code == 403

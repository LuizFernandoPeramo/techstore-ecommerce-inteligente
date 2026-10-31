
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

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_operacao_sem_token(
    client,
    banco_limpo,
    metodo
):
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

    headers = {
        "Authorization": "Bearer token-invalido"
    }

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
        resposta = client.delete(
            url,
            headers=headers
        )

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

    headers = obter_headers(
        client,
        cliente_1["email"]
    )

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
        resposta = client.delete(
            url,
            headers=headers
        )

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

    headers = obter_headers(
        client,
        cliente["email"]
    )

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

    headers = obter_headers(
        client,
        cliente["email"]
    )

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

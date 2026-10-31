
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import text

from app.core import security


SENHA_VALIDA = "TechStore@2026"


def cadastrar_cliente(client, numero=1, senha=SENHA_VALIDA):
    dados = {
        "nome": f"Cliente Autenticacao {numero}",
        "email": f"auth{numero}@exemplo.com",
        "telefone": "11999998888",
        "cpf": f"{numero:011d}"
    }

    if senha is not None:
        dados["senha"] = senha

    resposta = client.post("/clientes", json=dados)

    assert resposta.status_code == 201, resposta.text

    return resposta.json()


def fazer_login(client, email, senha):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": senha
        }
    )


def gerar_token_teste(cliente_id, expiracao):
    assert security.JWT_SECRET_KEY

    agora = datetime.now(timezone.utc)

    return jwt.encode(
        {
            "sub": str(cliente_id),
            "iat": agora,
            "exp": expiracao
        },
        security.JWT_SECRET_KEY,
        algorithm=security.JWT_ALGORITHM
    )


def test_cadastro_cliente_com_senha(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    assert cliente["id"] > 0
    assert cliente["email"] == "auth1@exemplo.com"
    assert "senha" not in cliente
    assert "senha_hash" not in cliente


def test_senha_armazenada_com_hash(
    client,
    test_engine,
    banco_limpo
):
    cliente = cadastrar_cliente(client)

    with test_engine.connect() as conexao:
        senha_hash = conexao.execute(
            text("""
                SELECT senha_hash
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente["id"]}
        ).scalar_one()

    assert senha_hash != SENHA_VALIDA
    assert senha_hash.startswith("$argon2")
    assert security.verificar_senha(
        SENHA_VALIDA,
        senha_hash
    )


def test_login_com_credenciais_validas(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    resposta = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta.status_code == 200, resposta.text

    dados = resposta.json()

    assert dados["token_type"] == "bearer"
    assert isinstance(dados["access_token"], str)
    assert len(dados["access_token"]) > 20

    cliente_id = security.validar_token_acesso(
        dados["access_token"]
    )

    assert cliente_id == cliente["id"]


def test_login_email_maiusculo(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    resposta = fazer_login(
        client,
        cliente["email"].upper(),
        SENHA_VALIDA
    )

    assert resposta.status_code == 200


def test_login_senha_incorreta(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    resposta = fazer_login(
        client,
        cliente["email"],
        "SenhaIncorreta123"
    )

    assert resposta.status_code == 401
    assert "access_token" not in resposta.json()


def test_login_email_inexistente(client, banco_limpo):
    resposta = fazer_login(
        client,
        "inexistente@exemplo.com",
        SENHA_VALIDA
    )

    assert resposta.status_code == 401


def test_login_cliente_sem_senha(client, banco_limpo):
    cliente = cadastrar_cliente(
        client,
        senha=None
    )

    resposta = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta.status_code == 401


def test_login_cliente_inativo(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    resposta_exclusao = client.delete(
        f"/clientes/{cliente['id']}"
    )

    assert resposta_exclusao.status_code == 200

    resposta = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "dados",
    [
        {
            "email": "email-invalido",
            "senha": SENHA_VALIDA
        },
        {
            "email": "auth@exemplo.com",
            "senha": ""
        },
        {
            "senha": SENHA_VALIDA
        },
        {
            "email": "auth@exemplo.com"
        }
    ]
)
def test_login_dados_invalidos(
    client,
    banco_limpo,
    dados
):
    resposta = client.post(
        "/auth/login",
        json=dados
    )

    assert resposta.status_code == 422


def test_me_com_token_valido(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    resposta_login = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta_login.status_code == 200

    token = resposta_login.json()["access_token"]

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["id"] == cliente["id"]
    assert resposta.json()["email"] == cliente["email"]
    assert "senha_hash" not in resposta.json()
    assert "senha" not in resposta.json()


def test_me_sem_token(client, banco_limpo):
    resposta = client.get("/auth/me")

    assert resposta.status_code in (401, 403)


def test_me_com_token_invalido(client, banco_limpo):
    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer token-invalido"
        }
    )

    assert resposta.status_code == 401


def test_me_com_token_expirado(client, banco_limpo):
    cliente = cadastrar_cliente(client)

    token = gerar_token_teste(
        cliente["id"],
        datetime.now(timezone.utc) - timedelta(minutes=5)
    )

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 401


def test_me_com_token_de_outro_cliente(
    client,
    banco_limpo
):
    cliente_1 = cadastrar_cliente(client, numero=1)
    cliente_2 = cadastrar_cliente(client, numero=2)

    token = gerar_token_teste(
        cliente_2["id"],
        datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cliente_2["id"]
    assert resposta.json()["id"] != cliente_1["id"]


def test_me_cliente_desativado_apos_login(
    client,
    banco_limpo
):
    cliente = cadastrar_cliente(client)

    resposta_login = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta_login.status_code == 200

    token = resposta_login.json()["access_token"]

    resposta_exclusao = client.delete(
        f"/clientes/{cliente['id']}"
    )

    assert resposta_exclusao.status_code == 200

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 401


def test_atualizacao_sem_senha_preserva_hash(
    client,
    test_engine,
    banco_limpo
):
    cliente = cadastrar_cliente(client)

    with test_engine.connect() as conexao:
        hash_original = conexao.execute(
            text("""
                SELECT senha_hash
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente["id"]}
        ).scalar_one()

    resposta = client.put(
        f"/clientes/{cliente['id']}",
        json={
            "nome": "Cliente Atualizado",
            "email": cliente["email"],
            "telefone": "11988887777",
            "cpf": "00000000001"
        }
    )

    assert resposta.status_code == 200, resposta.text

    with test_engine.connect() as conexao:
        hash_atual = conexao.execute(
            text("""
                SELECT senha_hash
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente["id"]}
        ).scalar_one()

    assert hash_atual == hash_original

    resposta_login = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert resposta_login.status_code == 200


def test_atualizacao_com_nova_senha(
    client,
    banco_limpo
):
    cliente = cadastrar_cliente(client)

    nova_senha = "NovaSenha@2026"

    resposta = client.put(
        f"/clientes/{cliente['id']}",
        json={
            "nome": cliente["nome"],
            "email": cliente["email"],
            "telefone": "11999998888",
            "cpf": "00000000001",
            "senha": nova_senha
        }
    )

    assert resposta.status_code == 200, resposta.text

    login_antigo = fazer_login(
        client,
        cliente["email"],
        SENHA_VALIDA
    )

    assert login_antigo.status_code == 401

    login_novo = fazer_login(
        client,
        cliente["email"],
        nova_senha
    )

    assert login_novo.status_code == 200


@pytest.mark.parametrize(
    "senha",
    [
        "1234567",
        "",
        "a" * 129
    ]
)
def test_cadastro_rejeita_senha_invalida(
    client,
    banco_limpo,
    senha
):
    resposta = client.post(
        "/clientes",
        json={
            "nome": "Cliente Senha Invalida",
            "email": "senha@exemplo.com",
            "cpf": "12345678901",
            "senha": senha
        }
    )

    assert resposta.status_code == 422


def test_token_com_identificador_invalido(
    client,
    banco_limpo
):
    token = gerar_token_teste(
        0,
        datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 401


def test_token_de_cliente_inexistente(
    client,
    banco_limpo
):
    token = gerar_token_teste(
        99999,
        datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    resposta = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 401

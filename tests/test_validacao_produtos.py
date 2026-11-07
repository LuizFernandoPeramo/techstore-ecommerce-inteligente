
import pytest
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


@pytest.fixture
def administrador_autenticado(client, test_engine):
    email = "admin.validacao@exemplo.com"

    resposta_cadastro = client.post(
        "/clientes",
        json={
            "nome": "Administrador Validacao",
            "email": email,
            "telefone": "11999998888",
            "cpf": "12345678901",
            "senha": SENHA_TESTE
        }
    )

    assert resposta_cadastro.status_code == 201, resposta_cadastro.text
    cliente_id = resposta_cadastro.json()["id"]

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

    resposta_login = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": SENHA_TESTE
        }
    )

    assert resposta_login.status_code == 200, resposta_login.text

    token = resposta_login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "produto_invalido",
    [
        {
            "nome": "AB",
            "categoria": "Monitores",
            "preco": 1200.00,
            "estoque": 10
        },
        {
            "nome": "Monitor LG",
            "categoria": "TI",
            "preco": 1200.00,
            "estoque": 10
        },
        {
            "nome": "Monitor LG",
            "categoria": "Monitores",
            "preco": 0,
            "estoque": 10
        },
        {
            "nome": "Monitor LG",
            "categoria": "Monitores",
            "preco": -150.00,
            "estoque": 10
        },
        {
            "nome": "Monitor LG",
            "categoria": "Monitores",
            "preco": 1200.00,
            "estoque": -5
        },
        {
            "nome": "Monitor LG",
            "categoria": "Monitores",
            "preco": 1200.999,
            "estoque": 10
        },
        {
            "nome": "Monitor LG",
            "categoria": "Monitores",
            "preco": 1200.00
        }
    ]
)
def test_cadastro_produto_invalido(
    client,
    banco_limpo,
    administrador_autenticado,
    produto_invalido
):
    resposta = client.post(
        "/produtos",
        json=produto_invalido,
        headers=administrador_autenticado
    )

    assert resposta.status_code == 422


def test_cadastro_produto_estoque_zero(
    client,
    banco_limpo,
    administrador_autenticado
):
    produto = {
        "nome": "Mouse Logitech",
        "categoria": "Acessorios",
        "preco": 79.90,
        "estoque": 0
    }

    resposta = client.post(
        "/produtos",
        json=produto,
        headers=administrador_autenticado
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Mouse Logitech"
    assert dados["estoque"] == 0

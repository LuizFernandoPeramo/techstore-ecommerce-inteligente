
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


BANCO_TESTES = "techstore_test_db"


@pytest.fixture(scope="session")
def test_engine():
    load_dotenv()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=BANCO_TESTES
    )

    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

    try:
        with engine.connect() as conexao:
            banco_atual = conexao.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if banco_atual != BANCO_TESTES:
                raise RuntimeError(
                    "Os testes nao estao conectados ao banco correto!"
                )

        yield engine

    finally:
        engine.dispose()


def limpar_banco_testes(test_engine):
    with test_engine.begin() as conexao:
        banco_atual = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco_atual != BANCO_TESTES:
            raise RuntimeError(
                "Limpeza bloqueada: banco de dados incorreto!"
            )

        conexao.execute(
            text("""
                TRUNCATE TABLE
                    pagamentos,
                    itens_carrinho,
                    carrinhos,
                    itens_pedido,
                    pedidos,
                    produtos,
                    clientes
                RESTART IDENTITY CASCADE
            """)
        )


@pytest.fixture
def banco_limpo(test_engine):
    limpar_banco_testes(test_engine)

    try:
        yield

    finally:
        limpar_banco_testes(test_engine)


@pytest.fixture
def client(test_engine, monkeypatch):
    import app.services.produto_service as produto_service
    import app.services.cliente_service as cliente_service
    import app.services.pedido_service as pedido_service
    import app.services.auth_service as auth_service
    import app.services.carrinho_service as carrinho_service
    import app.services.checkout_service as checkout_service
    import app.services.pagamento_service as pagamento_service

    services = (
        produto_service,
        cliente_service,
        pedido_service,
        auth_service,
        carrinho_service,
        checkout_service,
        pagamento_service
    )

    for service in services:
        monkeypatch.setattr(
            service,
            "engine",
            test_engine
        )

    from app.main import app

    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def cliente_autenticado(client):
    def autenticar(email, senha):
        resposta = client.post(
            "/auth/login",
            json={
                "email": email,
                "senha": senha
            }
        )

        assert resposta.status_code == 200, resposta.text

        token = resposta.json()["access_token"]

        return {
            "Authorization": f"Bearer {token}"
        }

    return autenticar

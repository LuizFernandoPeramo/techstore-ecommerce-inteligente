
import pytest


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
    produto_invalido
):
    resposta = client.post(
        "/produtos",
        json=produto_invalido
    )

    assert resposta.status_code == 422


def test_cadastro_produto_estoque_zero(client, banco_limpo):
    produto = {
        "nome": "Mouse Logitech",
        "categoria": "Acessorios",
        "preco": 79.90,
        "estoque": 0
    }

    resposta = client.post(
        "/produtos",
        json=produto
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Mouse Logitech"
    assert dados["estoque"] == 0



def test_pagina_inicial(client):
    resposta = client.get("/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["sistema"] == "TechStore"
    assert dados["status"] == "online"


def test_saude_api(client):
    resposta = client.get("/saude")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["status"] == "ok"
    assert dados["servico"] == "TechStore API"

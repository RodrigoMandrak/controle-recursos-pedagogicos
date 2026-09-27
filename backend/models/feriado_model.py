import requests


def buscar_feriados(ano):
    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"

    try:
        resposta = requests.get(url, timeout=5)

        if resposta.status_code != 200:
            return None

        return resposta.json()

    except requests.RequestException:
        return None


def verificar_feriado(data):
    ano = data[:4]

    feriados = buscar_feriados(ano)

    if feriados is None:
        return {
            "erro_api": True
        }

    for feriado in feriados:
        if feriado.get("date") == data:
            return {
                "feriado": True,
                "nome": feriado.get("name")
            }

    return {
        "feriado": False,
        "nome": None
    }
import requests
from datetime import datetime, timedelta


_cache_feriados = {}
TEMPO_CACHE_MINUTOS = 60

ANO_MINIMO = 2000
ANO_MAXIMO = 2100


def validar_data(data):
    if not data or not isinstance(data, str):
        return False

    try:
        data_convertida = datetime.strptime(data, "%Y-%m-%d")

        if data_convertida.strftime("%Y-%m-%d") != data:
            return False

        if data_convertida.year < ANO_MINIMO or data_convertida.year > ANO_MAXIMO:
            return False

        return True

    except ValueError:
        return False


def limpar_cache():
    _cache_feriados.clear()


def buscar_feriados(ano):
    ano = str(ano)
    agora = datetime.now()

    cache = _cache_feriados.get(ano)

    if cache and agora < cache["expira_em"]:
        return {
            "feriados": cache["feriados"],
            "origem": "cache"
        }

    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"

    try:
        resposta = requests.get(url, timeout=5)

        if resposta.status_code != 200:
            return None

        feriados = resposta.json()

        if not isinstance(feriados, list):
            return None

        _cache_feriados[ano] = {
            "feriados": feriados,
            "expira_em": agora + timedelta(minutes=TEMPO_CACHE_MINUTOS)
        }

        return {
            "feriados": feriados,
            "origem": "api"
        }

    except (requests.RequestException, ValueError):
        return None


def verificar_feriado(data):
    if not validar_data(data):
        return {
            "erro_data": True,
            "mensagem": "Data invalida. Informe uma data entre 2000 e 2100."
        }

    ano = data[:4]
    consulta = buscar_feriados(ano)

    if consulta is None:
        return {
            "erro_api": True
        }

    feriados = consulta["feriados"]
    origem = consulta["origem"]

    for feriado in feriados:
        if feriado.get("date") == data:
            return {
                "feriado": True,
                "nome": feriado.get("name"),
                "origem": origem
            }

    return {
        "feriado": False,
        "nome": None,
        "origem": origem
    }

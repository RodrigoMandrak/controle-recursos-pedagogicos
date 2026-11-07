import re
from datetime import date, datetime


# limites usados nos formularios
TAMANHO_MINIMO_SENHA = 8
TAMANHO_MINIMO_NOME = 3
TAMANHO_MAXIMO_NOME = 100
TAMANHO_MAXIMO_EMAIL = 150
TAMANHO_MAXIMO_IDENTIFICADOR = 50
TAMANHO_MAXIMO_DESCRICAO = 500

PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def email_valido(email):
    if not email or len(email) > TAMANHO_MAXIMO_EMAIL:
        return False

    return PADRAO_EMAIL.match(email) is not None


def senha_valida(senha):
    return senha is not None and len(senha) >= TAMANHO_MINIMO_SENHA


def nome_valido(nome):
    if not nome:
        return False

    tamanho = len(nome.strip())
    return TAMANHO_MINIMO_NOME <= tamanho <= TAMANHO_MAXIMO_NOME


def texto_no_limite(texto, limite):
    # campo opcional: vazio tambem vale
    if not texto:
        return True

    return len(texto) <= limite


def converter_data(texto):
    # devolve a data ou None se o formato estiver errado
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def horario_valido(texto):
    # aceita 08:30 e tambem 08:30:00
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            datetime.strptime(texto, formato)
            return True
        except (TypeError, ValueError):
            pass

    return False


def data_passada(data_atividade, hoje=None):
    if hoje is None:
        hoje = date.today()

    return data_atividade < hoje

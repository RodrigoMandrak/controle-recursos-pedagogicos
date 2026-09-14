from models.alocacao_model import pegar_atividade
from models.alocacao_model import procurar_conflito_recurso
from models.alocacao_model import procurar_conflito_professor
from models.alocacao_model import procurar_conflito_turma


def validar_conflitos(atividade_id, recurso_id):

    # primeiro pega os dados da atividade
    atividade = pegar_atividade(atividade_id)

    if not atividade:
        return "Atividade nao encontrada"

    data = atividade[0]
    inicio = atividade[1]
    fim = atividade[2]
    professor = atividade[3]
    turma = atividade[4]

    # debug pra conferir se chegou tudo certo
    print("testando conflitos:", atividade_id, recurso_id)

    conflito_recurso = procurar_conflito_recurso(
        recurso_id,
        data,
        inicio,
        fim
    )

    if conflito_recurso:
        print("conflito de recurso")

        return "Esse recurso ja esta sendo usado nesse horario"


    conflito_professor = procurar_conflito_professor(
        professor,
        atividade_id,
        data,
        inicio,
        fim
    )

    if conflito_professor:
        print("conflito de professor")

        return "Esse professor ja possui uma atividade nesse horario"


    conflito_turma = procurar_conflito_turma(
        turma,
        atividade_id,
        data,
        inicio,
        fim
    )

    if conflito_turma:
        print("conflito de turma")

        return "Essa turma ja possui uma atividade nesse horario"


    # parte do rapha, #### dps arrumar no front as colunas e separar melhor
    return None
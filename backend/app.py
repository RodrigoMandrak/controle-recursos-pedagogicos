from flask import Flask, request, jsonify
from flask_cors import CORS
from banco import conectar

app = Flask(__name__)
CORS(app)

@app.route("/")
def inicio():
    return "Sistema de Controle de Recursos Pedagogicos"


# TODO: criar uma middleware de erro no futuro se der tempo

@app.route("/atividades", methods=["POST"])
def cadastrar():
    dados = request.json
    # print(dados) # debug
    
    disciplina = dados.get("disciplina_id")
    turma = dados.get("turma_id")
    professor = dados.get("professor_id")
    descricao = dados.get("descricao")
    data = dados.get("data")
    inicio = dados.get("hora_inicio")
    fim = dados.get("hora_fim")

    # checa obrigatorios
    if not disciplina or not turma or not professor:
        return jsonify({"erro": "Preencha todos os dados"}), 400

    if not data or not inicio or not fim:
        return jsonify({"erro": "Preencha a data e o horario"}), 400

    if fim <= inicio:
        return jsonify({"erro": "Horario final invalido"}), 400

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        """INSERT INTO atividades 
        (disciplina_id, turma_id, professor_id, descricao, data, hora_inicio, hora_fim) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (disciplina, turma, professor, descricao, data, inicio, fim)
    )

    banco.commit()
    cursor.close()
    banco.close()

    return jsonify({"mensagem": "Atividade cadastrada"})


@app.route("/atividades", methods=["GET"])
def listar():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT a.id, d.nome, t.nome, p.nome, 
        a.descricao, a.data, a.hora_inicio, a.hora_fim
        FROM atividades a
        JOIN disciplinas d ON d.id = a.disciplina_id
        JOIN turmas t ON t.id = a.turma_id
        JOIN professores p ON p.id = a.professor_id
        ORDER BY a.id DESC
    """)

    dados = cursor.fetchall()
    
    lista = []
    for atividade in dados:
        lista.append({
            "id": atividade[0],
            "disciplina": atividade[1],
            "turma": atividade[2],
            "professor": atividade[3],
            "descricao": atividade[4],
            "data": str(atividade[5]),
            "hora_inicio": str(atividade[6]),
            "hora_fim": str(atividade[7])
        })

    cursor.close()
    banco.close()

    return jsonify(lista)


# --- AUXILIARES ---

@app.route("/disciplinas", methods=["GET"])
def listar_disciplinas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM disciplinas ORDER BY nome")
    dados = cursor.fetchall()

    # refatorei aqui pra economizar linha
    lista = [{"id": item[0], "nome": item[1]} for item in dados]

    cursor.close()
    banco.close()
    return jsonify(lista)


@app.route("/turmas", methods=["GET"])
def listar_turmas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM turmas ORDER BY nome")
    dados = cursor.fetchall()

    lista = []
    for item in dados:
        lista.append({"id": item[0], "nome": item[1]})

    cursor.close()
    banco.close()
    return jsonify(lista)


########################## kaique sua parte vai aqui em baixo não mistura// 
## e me avisa depois que finalizar os commit

@app.route("/professores", methods=["GET"])
def listar_professores():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM professores ORDER BY nome")
    dados = cursor.fetchall()

    lista = []
    for item in dados:
        lista.append({
            "id": item[0],
            "nome": item[1]
        })

    cursor.close()
    banco.close()
    return jsonify(lista)


@app.route("/recursos", methods=["GET"])
def listar_recursos():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome, tipo, status FROM recursos ORDER BY nome")
    dados = cursor.fetchall()

    lista = []
    for recurso in dados:
        lista.append({
            "id": recurso[0],
            "nome": recurso[1],
            "tipo": recurso[2],
            "status": recurso[3]
        })

    cursor.close()
    banco.close()

    return jsonify(lista)


# --- ALOCACOES ---

@app.route("/alocacoes", methods=["POST"])
def alocar_recurso():
    dados = request.json

    atividade = dados.get("atividade_id")
    recurso = dados.get("recurso_id")

    if not atividade or not recurso:
        return jsonify({"erro": "Escolha uma atividade e um recurso"}), 400

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s)",
        (atividade, recurso)
    )

    banco.commit()
    cursor.close()
    banco.close()

    # TODO: retornar o objeto criado em vez de só msg no front
    return jsonify({"mensagem": "Recurso alocado"})


@app.route("/alocacoes", methods=["GET"])
def listar_alocacoes():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT al.id, d.nome, t.nome, p.nome,
        a.data, a.hora_inicio, a.hora_fim,
        r.nome, r.tipo
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        JOIN disciplinas d ON d.id = a.disciplina_id
        JOIN turmas t ON t.id = a.turma_id
        JOIN professores p ON p.id = a.professor_id
        JOIN recursos r ON r.id = al.recurso_id
        ORDER BY al.id DESC
    """)

    dados = cursor.fetchall()
    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "disciplina": item[1],
            "turma": item[2],
            "professor": item[3],
            "data": str(item[4]),
            "hora_inicio": str(item[5]),
            "hora_fim": str(item[6]),
            "recurso": item[7],
            "tipo": item[8]
        })

    cursor.close()
    banco.close()

    return jsonify(lista)


if __name__ == "__main__":
    app.run(debug=True)
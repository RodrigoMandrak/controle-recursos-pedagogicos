from banco import conectar

try:
    conexao = conectar()
    print("Banco conectado com sucesso!")
    conexao.close()
except Exception as erro:
    print("Erro ao conectar:")
    print(erro)
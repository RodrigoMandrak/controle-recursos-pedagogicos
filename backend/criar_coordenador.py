from models.usuario_model import cadastrar_usuario


print("Criar usuario coordenador")

nome = input("Nome: ")
email = input("Email: ")
senha = input("Senha: ")

cadastrar_usuario(
    nome,
    email,
    senha,
    "coordenador"
)

print("Coordenador criado com sucesso")
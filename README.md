# Sistema de Controle de Recursos Pedagógicos

Sistema web para escolas organizarem as **atividades acadêmicas** e a **reserva de recursos pedagógicos**: laboratórios, salas, projetores, notebooks e kits. Ele impede que o mesmo recurso, professor ou turma fique em dois lugares no mesmo horário.

Projeto Final de Curso (PFC) de **Engenharia de Software** da **UMC – Universidade de Mogi das Cruzes**.

| | |
|---|---|
| **Integrantes** | Alyson Rodrigo Miguel Pereira · Kaique Barros Fernandes |
| **Orientador** | Prof. Lucas Santos da Silva |
| **Sistema online** | https://pfc-front.onrender.com |
| **API online** | https://pfc-back-rf0i.onrender.com |

> O sistema online usa o plano gratuito do Render. Depois de 15 minutos sem uso, o servidor "dorme", e o primeiro acesso pode levar cerca de 1 minuto. Se aparecer "Erro ao conectar com o servidor", aguarde e recarregue a página.

---

## Funcionalidades

**Professor**
- Pede acesso pelo cadastro e só entra depois que a coordenação aprova.
- Cadastra atividades sempre no próprio nome. Também pode alterá-las ou cancelá-las enquanto não aconteceram.
- Reserva um ou mais recursos para cada atividade.
- Vê o próprio dashboard, consulta os dados da conta e pode excluí-la (LGPD).

**Coordenador**
- Vê e gerencia as atividades e reservas de todos os professores.
- Cadastra recursos com **estoque**: um recurso com 3 unidades aceita até 3 reservas no mesmo horário. Também pode colocá-lo em manutenção.
- Cadastra, renomeia e exclui **disciplinas, turmas e professores** na aba *Dados acadêmicos*.
- Aprova ou recusa as solicitações de cadastro.
- Consulta os **logs de auditoria**, com filtros por ação, pessoa, texto e período, e paginação.
- Usa o dashboard com filtros por período e disciplina.

**Regras principais**
- **Conflito de horário:** a mesma turma ou o mesmo professor não pode ter duas atividades ao mesmo tempo. O recurso só é reservado se ainda houver unidade livre no horário. Dois horários batem quando `início novo < fim existente` **e** `fim novo > início existente`.
- **Concorrência:** a reserva trava o recurso no banco (`SELECT ... FOR UPDATE`), para duas pessoas não pegarem a última unidade no mesmo instante.
- **Devolução automática:** quando a aula termina, a unidade volta a ficar livre para os próximos horários.
- **Data e horário:** o sistema não aceita data passada nem horário final antes do inicial. Também avisa quando a data é feriado nacional, consultando a BrasilAPI.
- **Exclusão segura:** o que já foi usado em aulas antigas é **arquivado** (exclusão lógica), e o histórico continua correto. O que tem aula marcada para o futuro não pode ser excluído.
- **Segurança:**
  - senhas guardadas com hash;
  - sessão por cookie;
  - bloqueio de 5 minutos depois de 5 senhas erradas;
  - recuperação de senha por e-mail com link temporário;
  - aceite dos termos e da política de privacidade.
- **Auditoria:** cada ação importante fica registrada com quem fez e quando, inclusive as tentativas de conflito bloqueadas.

---

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Front-end | React · TanStack Start · Vite · Tailwind CSS · Recharts |
| Back-end | Python 3 · Flask (MVC com *blueprints*: controllers + models) · psycopg2 |
| Banco de dados | PostgreSQL |
| API externa | BrasilAPI (feriados nacionais) |
| Testes | pytest (unitários e de integração) |
| Hospedagem | Render (front e back) · Neon (PostgreSQL na nuvem) |

```
Navegador ──> Front-end (Render) ──/api──> Back-end Flask (Render) ──> PostgreSQL (Neon)
                                                  └──> BrasilAPI (feriados)
```

---

## Estrutura de pastas

```
backend/
  app.py               ponto de entrada da API (registra as rotas)
  banco.py             conexão com o PostgreSQL e atualização automática das tabelas
  validacoes.py        validações comuns (data, horário, e-mail, senha, tamanhos)
  controllers/         rotas da API (recebem a requisição, validam e respondem)
  models/              acesso ao banco (consultas SQL)
  tests/               testes unitários
  tests/integracao/    testes de integração (servidor real + banco de teste)
  preparar_banco.py    cria o banco, as tabelas, as contas e dados de demonstração
  turbinar_demo.py     (opcional) deixa o banco com 10 disciplinas, 10 recursos e 300 atividades antigas
frontend/
  src/routes/index.jsx telas de login, cadastro e área logada
  src/components/      Dashboard, Recursos, Solicitações, Dados acadêmicos, avisos...
diagramas/             BPMN e diagrama de classes
docs/                  documentação do projeto
```

---

## Como rodar no computador (Windows)

**Pré-requisitos:** Python 3, Node.js (versão LTS), PostgreSQL (com o pgAdmin, se quiser) e Git.

### 1. Baixar o projeto
```
git clone https://github.com/RodrigoMandrak/controle-recursos-pedagogicos.git
cd controle-recursos-pedagogicos
git checkout entrega1211
```

### 2. Back-end
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python preparar_banco.py
python app.py
```

O `preparar_banco.py`:
- pede a senha do PostgreSQL;
- cria o arquivo `.env`, o banco e as tabelas;
- cadastra dados de demonstração;
- cria uma conta de coordenador e uma de professor. Os e-mails e senhas dessas contas ficam no arquivo `ACESSOS_DEMONSTRACAO.txt`, que **não vai para o GitHub**.

Pode rodar o script mais de uma vez: ele não apaga nem duplica nada.

A API fica em `http://localhost:5000`.

Opcional, para deixar o dashboard cheio de dados:
```
python turbinar_demo.py
```

### 3. Front-end
Em outro terminal:
```
cd frontend
npm install
npm run dev
```
Abra **http://localhost:8080**.

### Variáveis de ambiente
O `.env` fica em `backend/.env` e é criado pelo `preparar_banco.py`. O modelo, sem nenhum valor real, está em [`backend/.env.example`](backend/.env.example).

| Variável | Para que serve |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | conexão com o PostgreSQL |
| `DB_SSLMODE` | `require` no banco da nuvem (Neon); no PC pode ficar vazio |
| `SECRET_KEY` | chave da sessão do Flask (texto aleatório e longo) |
| `FUSO_HORARIO` | padrão `America/Sao_Paulo` |
| `FRONTEND_URL` | endereço do site, usado no link de recuperação de senha |
| `EMAIL_REMETENTE`, `EMAIL_SENHA_APP` | Gmail e senha de app, para enviar a recuperação de senha |

No front-end, `VITE_API_URL` aponta para a API. Se não for definida, o front usa `http://localhost:5000`.

---

## Testes

Dentro de `backend`, com o venv ativo:

```
pip install -r requirements-test.txt
python -m pytest tests --ignore=tests/integracao
```

Os **testes unitários** (219) não precisam de banco: o acesso ao banco é simulado.

Os **testes de integração** sobem o servidor de verdade e usam um banco de teste temporário. O banco se chama `pfc_test_...`, é criado no começo e apagado no fim, e o banco do sistema nunca é usado. Eles precisam do PostgreSQL ligado:

```
python -m pytest tests/integracao
```

Para ver a cobertura de código:
```
pip install pytest-cov
python -m pytest tests --cov=. --cov-report=term
```

---

## Como verificar as funcionalidades

1. Entre como **coordenador**, com a conta do `ACESSOS_DEMONSTRACAO.txt` ou a do ambiente online fornecida à banca.
2. **Dashboard:** filtre por período e por disciplina.
3. **Dados acadêmicos:** cadastre uma turma, renomeie e exclua. Tente cadastrar uma disciplina que já existe para ver a mensagem de erro.
4. **Recursos e estoque:** cadastre um recurso com 2 unidades.
5. **Nova atividade:** cadastre uma atividade para daqui a alguns dias e reserve o recurso em **Alocar recurso**.
6. **Conflito:** cadastre outra atividade no mesmo horário com o mesmo professor ou a mesma turma. O sistema bloqueia.
7. **Estoque:** reserve o mesmo recurso em mais atividades no mesmo horário. Quando as unidades acabam, o sistema avisa.
8. **Alterar e cancelar:** em *Atividades cadastradas*, altere o horário e depois cancele. Os recursos ficam livres.
9. **Pré-cadastro:** numa janela anônima, crie uma conta de professor. Tente entrar e veja o aviso de que o cadastro aguarda aprovação. Como coordenador, aprove em *Solicitações de cadastro*.
10. **Logs de auditoria:** filtre por "Conflito bloqueado" e navegue entre as páginas.

---

## Hospedagem

- **Banco:** Neon (PostgreSQL), região US East 2.
- **Back-end:** Render (Web Service), pasta `backend`. As dependências estão em `requirements-render.txt`, que inclui o `gunicorn`. As variáveis de ambiente da tabela acima ficam no painel do Render, e não no código.
- **Front-end:** Render (Web Service), pasta `frontend`. A variável `API_ORIGEM` aponta para o endereço do back-end: o front repassa as chamadas de `/api` para ele.

Cada `git push` na branch publicada gera um novo deploy automático. Quando o back-end liga, ele confere e cria sozinho as colunas novas do banco (`atualizar_estrutura` em `banco.py`). Por isso, não é preciso rodar nenhum script no servidor depois de uma atualização.

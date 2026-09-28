import { createFileRoute } from "@tanstack/react-router";

import { useState, useEffect } from "react";

const API = "http://localhost:5000";



export const Route = createFileRoute("/")({

  component: Index,

  head: () => ({

    meta: [

      { title: "Agenda Pedagógica · Cadastro de Atividades" },

      {

        name: "description",

        content:

          "Cadastre e visualize atividades acadêmicas de forma simples, como anotar no caderno da sala de aula.",

      },

      {

        property: "og:title",

        content: "Agenda Pedagógica · Cadastro de Atividades",

      },

      {

        property: "og:description",

        content:

          "Cadastre e visualize atividades acadêmicas de forma simples, como anotar no caderno da sala de aula.",

      },

      { property: "og:type", content: "website" },

      { name: "twitter:card", content: "summary_large_image" },

    ],

  }),

});





const badgeStyles = {

  Matemática: "bg-green/15 text-[#4f7a63]",

  Literatura: "bg-blue/15 text-[#557c95]",

  Ciências: "bg-cream/40 text-[#8a6b2e]",

  "Banco de Dados": "bg-green/15 text-[#4f7a63]",

};



function getBadgeStyle(disciplina) {

  return badgeStyles[disciplina] || "bg-paper text-ink";

}



const months = [

  "janeiro",

  "fevereiro",

  "março",

  "abril",

  "maio",

  "junho",

  "julho",

  "agosto",

  "setembro",

  "outubro",

  "novembro",

  "dezembro",

];



function formatDate(dateString) {

  if (!dateString) return "";

  const [year, month, day] = dateString.split("-");

  return `${day} de ${months[parseInt(month, 10) - 1]}`;

}


function ModalDocumento({ tipo, fechar }) {
  if (!tipo) return null;

  const politica = tipo === "privacidade";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
      <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8">
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-line pb-4">
          <div>
            <h2 className="text-xl font-bold">
              {politica ? "Política de Privacidade" : "Termos de Uso"}
            </h2>
            <p className="mt-1 text-sm text-mute">Agenda Pedagógica</p>
          </div>

          <button
            type="button"
            onClick={fechar}
            className="rounded-xl bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line"
          >
            Fechar
          </button>
        </div>

        {politica ? (
          <div className="space-y-5 text-sm leading-relaxed text-ink/85">
            <div>
              <h3 className="font-semibold text-ink">1. Dados utilizados</h3>
              <p className="mt-1">
                O sistema utiliza nome, e-mail e, quando informado, identificador institucional.
                Também registra data e hora do aceite dos termos e ações importantes realizadas no sistema.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">2. Para que os dados são usados</h3>
              <p className="mt-1">
                O nome identifica o usuário nas atividades e registros. O e-mail é usado para acesso à conta.
                O identificador institucional, quando preenchido, auxilia na vinculação com o ambiente acadêmico.
                Os logs são usados para segurança, rastreabilidade e auditoria das ações realizadas.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">3. Proteção das informações</h3>
              <p className="mt-1">
                A senha não é armazenada em texto puro: o sistema guarda somente o hash da senha.
                O acesso às funcionalidades também é controlado por perfil de usuário, diferenciando professor e coordenador.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">4. Compartilhamento e acesso</h3>
              <p className="mt-1">
                Os dados são utilizados apenas nas funções do sistema acadêmico. Professores têm acesso limitado
                às próprias informações operacionais, enquanto o coordenador possui acesso administrativo conforme sua função.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">5. Direitos do usuário</h3>
              <p className="mt-1">
                O usuário pode solicitar consulta, correção ou exclusão dos dados da conta. A opção de exclusão
                será disponibilizada na área da conta e exigirá confirmação antes da remoção. Quando necessário para
                preservar a integridade de registros de auditoria, informações identificadoras poderão ser desvinculadas ou anonimizadas.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">6. Retenção</h3>
              <p className="mt-1">
                Os dados são mantidos enquanto a conta estiver ativa ou enquanto forem necessários para as finalidades
                acadêmicas e de segurança descritas nesta política.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-5 text-sm leading-relaxed text-ink/85">
            <div>
              <h3 className="font-semibold text-ink">1. Uso do sistema</h3>
              <p className="mt-1">
                A Agenda Pedagógica é destinada ao controle de atividades e recursos pedagógicos.
                O usuário deve utilizar sua própria conta e informar dados corretos no cadastro.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">2. Perfis e permissões</h3>
              <p className="mt-1">
                Contas comuns são cadastradas como professor. O perfil de coordenador possui permissões administrativas
                adicionais e não pode ser escolhido livremente durante o cadastro.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">3. Responsabilidade de acesso</h3>
              <p className="mt-1">
                O usuário deve manter sua senha em sigilo e encerrar a sessão ao terminar o uso em computadores compartilhados.
                Ações relevantes podem ser registradas para fins de auditoria e segurança.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">4. Uso adequado</h3>
              <p className="mt-1">
                Não é permitido tentar acessar registros de outros usuários sem autorização, manipular informações
                de forma indevida ou utilizar o sistema fora de sua finalidade acadêmica.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-ink">5. Privacidade</h3>
              <p className="mt-1">
                O tratamento dos dados pessoais utilizados pelo sistema é explicado na Política de Privacidade.
                Ao criar a conta, o usuário confirma que teve acesso a estes termos e à política.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



function Index() {

  const [usuario, setUsuario] = useState(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(true);
  const [erroLogin, setErroLogin] = useState("");
  const [loginForm, setLoginForm] = useState({
    email: "",
    senha: "",
  });

  const tokenInicial = typeof window !== "undefined"
    ? new URLSearchParams(window.location.search).get("redefinir") || ""
    : "";

  const [modoAcesso, setModoAcesso] = useState(tokenInicial ? "redefinir" : "login");
  const [documentoAberto, setDocumentoAberto] = useState(null);
  const [meusDadosAberto, setMeusDadosAberto] = useState(false);
  const [meusDados, setMeusDados] = useState(null);
  const [carregandoDados, setCarregandoDados] = useState(false);
  const [senhaExclusao, setSenhaExclusao] = useState("");
  const [erroExclusao, setErroExclusao] = useState("");
  const [erroCadastro, setErroCadastro] = useState("");
  const [logsAberto, setLogsAberto] = useState(false);
  const [logs, setLogs] = useState([]);
  const [carregandoLogs, setCarregandoLogs] = useState(false);

  const [recuperacaoEmail, setRecuperacaoEmail] = useState("");
  const [mensagemRecuperacao, setMensagemRecuperacao] = useState("");
  const [erroRecuperacao, setErroRecuperacao] = useState("");
  const [tokenRedefinicao, setTokenRedefinicao] = useState(tokenInicial);
  const [novaSenhaForm, setNovaSenhaForm] = useState({
    senha: "",
    confirmar_senha: "",
  });
  const [erroRedefinicao, setErroRedefinicao] = useState("");

  const [cadastroForm, setCadastroForm] = useState({
    nome: "",
    email: "",
    senha: "",
    confirmar_senha: "",
    identificador_institucional: "",
    aceitou_termos: false,
  });

  const [activities, setActivities] = useState([]);

  const [disciplinas, setDisciplinas] = useState([]);

const [turmas, setTurmas] = useState([]);

const [professores, setProfessores] = useState([]);

const [recursos, setRecursos] = useState([]);

const [alocacoes, setAlocacoes] = useState([]);

const [atividadeEscolhida, setAtividadeEscolhida] = useState("");

const [recursoEscolhido, setRecursoEscolhido] = useState("");

const [editandoAlocacao, setEditandoAlocacao] = useState(null);
const [novoRecurso, setNovoRecurso] = useState("");

const [paginaAlocacoes, setPaginaAlocacoes] = useState(1);
const [paginaAtividades, setPaginaAtividades] = useState(1);

const itensPorPagina = 5;

  const [form, setForm] = useState({

    disciplina: "",

    turma: "",

    professor: "",

    data: "",

    horarioInicial: "",

    horarioFinal: "",

    descricao: "",

  });

  const [feriado, setFeriado] = useState(null);
  const [consultandoFeriado, setConsultandoFeriado] = useState(false);

async function carregarAtividades() {

  try {

    const resposta = await fetch(`${API}/atividades`, { credentials: "include" });

    const dados = await resposta.json();



    const lista = dados.map((item) => ({

      id: item.id,

      disciplina: item.disciplina,

      turma: item.turma,

      professor: item.professor,

      descricao: item.descricao,

      data: item.data,

      horarioInicial: item.hora_inicio,

      horarioFinal: item.hora_fim,

    }));



    setActivities(lista);

  } catch (erro) {

    console.log("Erro ao carregar atividades", erro);

  }

}



async function carregarOpcoes() {

  try {

    const respostaDisciplinas = await fetch(`${API}/disciplinas`, { credentials: "include" });

    const dadosDisciplinas = await respostaDisciplinas.json();

    setDisciplinas(dadosDisciplinas);



    const respostaTurmas = await fetch(`${API}/turmas`, { credentials: "include" });

    const dadosTurmas = await respostaTurmas.json();

    setTurmas(dadosTurmas);



    const respostaProfessores = await fetch(`${API}/professores`, { credentials: "include" });

    const dadosProfessores = await respostaProfessores.json();

    setProfessores(dadosProfessores);



  } catch (erro) {

    console.log("Erro ao carregar dados", erro);

  }

}

async function carregarRecursos() {

    try {

        const resposta = await fetch(`${API}/recursos`, { credentials: "include" });

        const dados = await resposta.json();



        setRecursos(dados);

    } catch (erro) {

        console.log("Erro ao carregar recursos", erro);

    }

}



async function carregarAlocacoes() {

    try {

        const resposta = await fetch(`${API}/alocacoes`, { credentials: "include" });

        const dados = await resposta.json();



        setAlocacoes(dados);

    } catch (erro) {

        console.log("Erro ao carregar alocacoes", erro);

    }

}

async function verificarUsuario() {
  try {
    const resposta = await fetch(`${API}/usuario-logado`, {
      credentials: "include",
    });

    if (!resposta.ok) {
      setUsuario(null);
      return;
    }

    const dados = await resposta.json();
    setUsuario(dados);
  } catch (erro) {
    console.log("Erro ao verificar usuario", erro);
    setUsuario(null);
  } finally {
    setCarregandoUsuario(false);
  }
}

async function fazerLogin(e) {
  e.preventDefault();
  setErroLogin("");

  try {
    const resposta = await fetch(`${API}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(loginForm),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      setErroLogin(resultado.erro || "Nao foi possivel entrar");
      return;
    }

    setUsuario(resultado.usuario);
    setLoginForm({ email: "", senha: "" });
  } catch (erro) {
    console.log("Erro no login", erro);
    setErroLogin("Erro ao conectar com o servidor");
  }
}

async function solicitarRecuperacao(e) {
  e.preventDefault();
  setErroRecuperacao("");
  setMensagemRecuperacao("");

  if (!recuperacaoEmail.trim()) {
    setErroRecuperacao("Informe seu e-mail");
    return;
  }

  try {
    const resposta = await fetch(`${API}/esqueci-senha`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: recuperacaoEmail.trim() }),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      setErroRecuperacao(resultado.erro || "Nao foi possivel solicitar a recuperacao");
      return;
    }

    setMensagemRecuperacao(resultado.mensagem);
  } catch (erro) {
    console.log("Erro na recuperacao de senha", erro);
    setErroRecuperacao("Erro ao conectar com o servidor");
  }
}

async function redefinirSenha(e) {
  e.preventDefault();
  setErroRedefinicao("");

  if (novaSenhaForm.senha !== novaSenhaForm.confirmar_senha) {
    setErroRedefinicao("As senhas nao conferem");
    return;
  }

  if (novaSenhaForm.senha.length < 8) {
    setErroRedefinicao("A senha deve ter pelo menos 8 caracteres");
    return;
  }

  try {
    const resposta = await fetch(`${API}/redefinir-senha`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: tokenRedefinicao,
        senha: novaSenhaForm.senha,
        confirmar_senha: novaSenhaForm.confirmar_senha,
      }),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      setErroRedefinicao(resultado.erro || "Nao foi possivel redefinir a senha");
      return;
    }

    try {
      await fetch(`${API}/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (erro) {
      console.log("Erro ao encerrar sessao depois da redefinicao", erro);
    }

    alert("Senha redefinida com sucesso! Entre com a nova senha.");

    setUsuario(null);
    setNovaSenhaForm({ senha: "", confirmar_senha: "" });
    setTokenRedefinicao("");
    setModoAcesso("login");

    if (typeof window !== "undefined") {
      window.history.replaceState({}, "", window.location.pathname);
    }
  } catch (erro) {
    console.log("Erro ao redefinir senha", erro);
    setErroRedefinicao("Erro ao conectar com o servidor");
  }
}

function voltarParaLogin() {
  setModoAcesso("login");
  setErroRecuperacao("");
  setMensagemRecuperacao("");
  setErroRedefinicao("");
  setTokenRedefinicao("");

  if (typeof window !== "undefined") {
    window.history.replaceState({}, "", window.location.pathname);
  }
}

async function fazerCadastro(e) {
  e.preventDefault();
  setErroCadastro("");

  if (cadastroForm.senha !== cadastroForm.confirmar_senha) {
    setErroCadastro("As senhas nao conferem");
    return;
  }

  if (!cadastroForm.aceitou_termos) {
    setErroCadastro("Voce precisa aceitar os Termos de Uso e a Politica de Privacidade");
    return;
  }

  try {
    const resposta = await fetch(`${API}/usuarios/cadastro`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(cadastroForm),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      setErroCadastro(resultado.erro || "Nao foi possivel criar a conta");
      return;
    }

    alert("Conta criada com sucesso! Agora faca seu login.");

    setLoginForm({
      email: cadastroForm.email,
      senha: "",
    });

    setCadastroForm({
      nome: "",
      email: "",
      senha: "",
      confirmar_senha: "",
      identificador_institucional: "",
      aceitou_termos: false,
    });

    setModoAcesso("login");
  } catch (erro) {
    console.log("Erro no cadastro", erro);
    setErroCadastro("Erro ao conectar com o servidor");
  }
}

async function abrirLogs() {
  setLogsAberto(true);
  setCarregandoLogs(true);

  try {
    const resposta = await fetch(`${API}/logs`, {
      credentials: "include",
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      alert(resultado.erro || "Nao foi possivel carregar os logs");
      setLogsAberto(false);
      return;
    }

    setLogs(resultado);
  } catch (erro) {
    console.log("Erro ao carregar logs", erro);
    alert("Erro ao conectar com o servidor");
    setLogsAberto(false);
  } finally {
    setCarregandoLogs(false);
  }
}

async function fazerLogout() {
  try {
    await fetch(`${API}/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (erro) {
    console.log("Erro ao sair", erro);
  }

  setUsuario(null);
  setActivities([]);
  setAlocacoes([]);
  setRecursos([]);
}

async function abrirMeusDados() {
  setMeusDadosAberto(true);
  setCarregandoDados(true);
  setErroExclusao("");
  setSenhaExclusao("");

  try {
    const resposta = await fetch(`${API}/meus-dados`, {
      credentials: "include",
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      alert(resultado.erro || "Nao foi possivel carregar seus dados");
      setMeusDadosAberto(false);
      return;
    }

    setMeusDados(resultado);
  } catch (erro) {
    console.log("Erro ao carregar meus dados", erro);
    alert("Erro ao conectar com o servidor");
    setMeusDadosAberto(false);
  } finally {
    setCarregandoDados(false);
  }
}

async function excluirMinhaConta() {
  setErroExclusao("");

  if (!senhaExclusao) {
    setErroExclusao("Digite sua senha para confirmar a exclusao");
    return;
  }

  const confirmou = window.confirm(
    "Tem certeza que deseja excluir sua conta? Essa acao nao pode ser desfeita."
  );

  if (!confirmou) {
    return;
  }

  try {
    const resposta = await fetch(`${API}/minha-conta`, {
      method: "DELETE",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ senha: senhaExclusao }),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      setErroExclusao(resultado.erro || "Nao foi possivel excluir a conta");
      return;
    }

    alert("Conta excluida com sucesso");
    setMeusDadosAberto(false);
    setMeusDados(null);
    setSenhaExclusao("");
    setUsuario(null);
    setActivities([]);
    setAlocacoes([]);
    setRecursos([]);
  } catch (erro) {
    console.log("Erro ao excluir conta", erro);
    setErroExclusao("Erro ao conectar com o servidor");
  }
}

useEffect(() => {
  verificarUsuario();
}, []);

useEffect(() => {
  if (!usuario) {
    return;
  }

  carregarAtividades();
  carregarOpcoes();
  carregarRecursos();
  carregarAlocacoes();
}, [usuario]);



  async function verificarDataFeriado(data) {
    if (!data) {
      setFeriado(null);
      return;
    }

    setConsultandoFeriado(true);

    try {
      const resposta = await fetch(
        `${API}/verificar-feriado?data=${encodeURIComponent(data)}`,
        { credentials: "include" }
      );

      const resultado = await resposta.json();

      if (!resposta.ok) {
        console.log("Nao foi possivel consultar o feriado", resultado.erro);
        setFeriado(null);
        return;
      }

      setFeriado(resultado);
    } catch (erro) {
      console.log("Erro ao consultar feriado", erro);
      setFeriado(null);
    } finally {
      setConsultandoFeriado(false);
    }
  }

  function handleChange(e) {

    const { name, value } = e.target;

    setForm((prev) => ({ ...prev, [name]: value }));

    if (name === "data") {
      verificarDataFeriado(value);
    }

  }



  async function handleSubmit(e) {

  e.preventDefault();



 const dados = {

  disciplina_id: Number(form.disciplina),

  turma_id: Number(form.turma),

  professor_id: Number(form.professor),

  descricao: form.descricao,

  data: form.data,

  hora_inicio: form.horarioInicial,

  hora_fim: form.horarioFinal,

};



  try {

    const resposta = await fetch(`${API}/atividades`, {

      method: "POST",

      credentials: "include",

      headers: {

        "Content-Type": "application/json",

      },

      body: JSON.stringify(dados),

    });



    const resultado = await resposta.json();



    if (!resposta.ok) {

      alert(resultado.erro);

      return;

    }



    alert("Atividade cadastrada com sucesso!");

    await carregarAtividades();
    setPaginaAtividades(1);

    setForm({

      disciplina: "",

      turma: "",

      professor: "",

      data: "",

      horarioInicial: "",

      horarioFinal: "",

      descricao: "",

    });

    setFeriado(null);



  } catch (erro) {

    alert("Erro ao conectar com o servidor");

    console.log(erro);

  }

}

async function salvarAlocacao(e) {

 e.preventDefault();



 if (!atividadeEscolhida || !recursoEscolhido) {

   alert("Escolha uma atividade e um recurso");

   return;

 }



 const dados = {

   atividade_id: Number(atividadeEscolhida),

   recurso_id: Number(recursoEscolhido)

 };



 try {

   const resposta = await fetch(`${API}/alocacoes`, {

     method: "POST",

     credentials: "include",

     headers: {

       "Content-Type": "application/json"

     },

     body: JSON.stringify(dados)

   });



   const resultado = await resposta.json();



   if (!resposta.ok) {

     alert(resultado.erro);

     return;

   }



   alert("Recurso alocado com sucesso!");



   setAtividadeEscolhida("");

   setRecursoEscolhido("");

   setPaginaAlocacoes(1);
   carregarAlocacoes();



 } catch (erro) {

   alert("Erro ao fazer a alocacao");

   console.log(erro);

 }

}


async function cancelarAlocacao(id) {

  const confirmar = window.confirm(
    "Deseja realmente cancelar essa alocacao?"
  );

  if (!confirmar) {
    return;
  }

  try {

    const resposta = await fetch(
      `${API}/alocacoes/${id}`,
      {
        method: "DELETE",
        credentials: "include"
      }
    );

    const resultado = await resposta.json();

    if (!resposta.ok) {
      alert(resultado.erro);
      return;
    }

    alert("Alocacao cancelada");

    setPaginaAlocacoes(1);
    carregarAlocacoes();

  } catch (erro) {

    alert("Erro ao cancelar alocacao");
    console.log(erro);

  }
}


async function alterarAlocacao(id) {

  if (!novoRecurso) {
    alert("Escolha um novo recurso");
    return;
  }

  const dados = {
    recurso_id: Number(novoRecurso)
  };

  try {

    const resposta = await fetch(
      `${API}/alocacoes/${id}`,
      {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(dados)
      }
    );

    const resultado = await resposta.json();

    if (!resposta.ok) {
      alert(resultado.erro);
      return;
    }

    alert("Alocacao alterada");

    setEditandoAlocacao(null);
    setNovoRecurso("");

    carregarAlocacoes();

  } catch (erro) {

    alert("Erro ao alterar alocacao");
    console.log(erro);

  }
}


const inicioAlocacoes = (paginaAlocacoes - 1) * itensPorPagina;
const fimAlocacoes = inicioAlocacoes + itensPorPagina;

const alocacoesPagina = alocacoes.slice(
  inicioAlocacoes,
  fimAlocacoes
);

const totalPaginasAlocacoes = Math.ceil(
  alocacoes.length / itensPorPagina
);


const inicioAtividades = (paginaAtividades - 1) * itensPorPagina;
const fimAtividades = inicioAtividades + itensPorPagina;

const atividadesPagina = activities.slice(
  inicioAtividades,
  fimAtividades
);

const totalPaginasAtividades = Math.ceil(
  activities.length / itensPorPagina
);

  if (carregandoUsuario) {
    return (
      <main className="min-h-screen bg-paper font-sans text-ink antialiased">
        <div className="mx-auto flex min-h-screen max-w-md items-center px-5">
          <p className="w-full text-center text-sm text-mute">Carregando...</p>
        </div>
      </main>
    );
  }

  if (modoAcesso === "redefinir" && tokenRedefinicao) {
    return (
      <main className="min-h-screen bg-paper font-sans text-ink antialiased">
        <div className="mx-auto flex min-h-screen max-w-md items-center px-5 py-12">
          <div className="w-full">
            <header className="mb-8 text-center">
              <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-card ring-1 ring-line">
                <span className="font-hand text-3xl leading-none text-green">Ag</span>
              </span>
              <h1 className="mt-4 text-2xl font-bold">Criar nova senha</h1>
              <p className="mt-2 text-sm text-mute">
                Digite a nova senha para sua conta.
              </p>
            </header>

            <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8">
              <form onSubmit={redefinirSenha} className="space-y-4">
                <label className="block">
                  <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                    Nova senha
                  </span>
                  <input
                    type="password"
                    value={novaSenhaForm.senha}
                    onChange={(e) =>
                      setNovaSenhaForm({ ...novaSenhaForm, senha: e.target.value })
                    }
                    placeholder="Minimo de 8 caracteres"
                    required
                    className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                  />
                </label>

                <label className="block">
                  <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                    Confirmar nova senha
                  </span>
                  <input
                    type="password"
                    value={novaSenhaForm.confirmar_senha}
                    onChange={(e) =>
                      setNovaSenhaForm({
                        ...novaSenhaForm,
                        confirmar_senha: e.target.value,
                      })
                    }
                    placeholder="Repita a nova senha"
                    required
                    className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                  />
                </label>

                {erroRedefinicao && (
                  <p className="rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line">
                    {erroRedefinicao}
                  </p>
                )}

                <button
                  type="submit"
                  className="w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white"
                >
                  Salvar nova senha
                </button>

                <button
                  type="button"
                  onClick={voltarParaLogin}
                  className="w-full text-sm font-semibold text-green underline underline-offset-2"
                >
                  Voltar para o login
                </button>
              </form>
            </section>
          </div>
        </div>
      </main>
    );
  }

  if (!usuario && modoAcesso === "recuperacao") {
    return (
      <main className="min-h-screen bg-paper font-sans text-ink antialiased">
        <div className="mx-auto flex min-h-screen max-w-md items-center px-5 py-12">
          <div className="w-full">
            <header className="mb-8 text-center">
              <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-card ring-1 ring-line">
                <span className="font-hand text-3xl leading-none text-green">Ag</span>
              </span>
              <h1 className="mt-4 text-2xl font-bold">Recuperar senha</h1>
              <p className="mt-2 text-sm text-mute">
                Informe o e-mail da sua conta para receber um link temporario.
              </p>
            </header>

            <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8">
              <form onSubmit={solicitarRecuperacao} className="space-y-4">
                <label className="block">
                  <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                    E-mail
                  </span>
                  <input
                    type="email"
                    value={recuperacaoEmail}
                    onChange={(e) => setRecuperacaoEmail(e.target.value)}
                    placeholder="seuemail@exemplo.com"
                    required
                    className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                  />
                </label>

                {erroRecuperacao && (
                  <p className="rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line">
                    {erroRecuperacao}
                  </p>
                )}

                {mensagemRecuperacao && (
                  <p className="rounded-xl bg-green/10 px-3.5 py-2.5 text-sm text-ink ring-1 ring-green/30">
                    {mensagemRecuperacao}
                  </p>
                )}

                <button
                  type="submit"
                  className="w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white"
                >
                  Enviar link de recuperacao
                </button>

                <button
                  type="button"
                  onClick={voltarParaLogin}
                  className="w-full text-sm font-semibold text-green underline underline-offset-2"
                >
                  Voltar para o login
                </button>
              </form>
            </section>
          </div>
        </div>
      </main>
    );
  }

  if (!usuario) {
    return (
      <main className="min-h-screen bg-paper font-sans text-ink antialiased">
        <div className="mx-auto flex min-h-screen max-w-md items-center px-5 py-12">
          <div className="w-full">
            <header className="mb-8 text-center">
              <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-card ring-1 ring-line">
                <span className="font-hand text-3xl leading-none text-green">Ag</span>
              </span>

              <h1 className="mt-4 text-2xl font-bold">Agenda Pedagógica</h1>
              <p className="mt-2 text-sm text-mute">
                Entre com sua conta para acessar o sistema
              </p>
            </header>

            <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8">
              <div className="mb-6 border-b border-line pb-4">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setModoAcesso("login");
                      setErroLogin("");
                    }}
                    className={`rounded-xl px-4 py-2 text-sm font-semibold ${
                      modoAcesso === "login"
                        ? "bg-green text-white"
                        : "bg-paper text-ink ring-1 ring-line"
                    }`}
                  >
                    Entrar
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setModoAcesso("cadastro");
                      setErroCadastro("");
                    }}
                    className={`rounded-xl px-4 py-2 text-sm font-semibold ${
                      modoAcesso === "cadastro"
                        ? "bg-green text-white"
                        : "bg-paper text-ink ring-1 ring-line"
                    }`}
                  >
                    Criar conta
                  </button>
                </div>

                <p className="mt-4 text-sm text-mute">
                  {modoAcesso === "login"
                    ? "Use seu e-mail e sua senha cadastrados."
                    : "Preencha os dados abaixo para criar sua conta de professor."}
                </p>
              </div>

              {modoAcesso === "login" ? (
                <form onSubmit={fazerLogin} className="space-y-4">
                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                      E-mail
                    </span>
                    <input
                      type="email"
                      value={loginForm.email}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, email: e.target.value })
                      }
                      placeholder="seuemail@exemplo.com"
                      required
                      className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line placeholder:text-mute/60 focus:outline-none focus:ring-2 focus:ring-green"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                      Senha
                    </span>
                    <input
                      type="password"
                      value={loginForm.senha}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, senha: e.target.value })
                      }
                      placeholder="Digite sua senha"
                      required
                      className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line placeholder:text-mute/60 focus:outline-none focus:ring-2 focus:ring-green"
                    />
                  </label>

                  {erroLogin && (
                    <p className="rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line">
                      {erroLogin}
                    </p>
                  )}

                  <button
                    type="submit"
                    className="w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white transition-colors duration-200 hover:bg-[#5f8871]"
                  >
                    Entrar
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setModoAcesso("recuperacao");
                      setRecuperacaoEmail(loginForm.email);
                      setErroRecuperacao("");
                      setMensagemRecuperacao("");
                    }}
                    className="w-full text-center text-sm font-semibold text-green underline underline-offset-2"
                  >
                    Esqueci minha senha
                  </button>
                </form>
              ) : (
                <form onSubmit={fazerCadastro} className="space-y-4">
                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                      Nome
                    </span>
                    <input
                      type="text"
                      value={cadastroForm.nome}
                      onChange={(e) =>
                        setCadastroForm({ ...cadastroForm, nome: e.target.value })
                      }
                      placeholder="Seu nome completo"
                      required
                      className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                      E-mail
                    </span>
                    <input
                      type="email"
                      value={cadastroForm.email}
                      onChange={(e) =>
                        setCadastroForm({ ...cadastroForm, email: e.target.value })
                      }
                      placeholder="seuemail@exemplo.com"
                      required
                      className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                      Identificador institucional (opcional)
                    </span>
                    <input
                      type="text"
                      value={cadastroForm.identificador_institucional}
                      onChange={(e) =>
                        setCadastroForm({
                          ...cadastroForm,
                          identificador_institucional: e.target.value,
                        })
                      }
                      placeholder="Matricula ou codigo institucional"
                      className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                    />
                  </label>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <label className="block">
                      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                        Senha
                      </span>
                      <input
                        type="password"
                        value={cadastroForm.senha}
                        onChange={(e) =>
                          setCadastroForm({ ...cadastroForm, senha: e.target.value })
                        }
                        placeholder="Digite sua senha"
                        required
                        className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">
                        Confirmar senha
                      </span>
                      <input
                        type="password"
                        value={cadastroForm.confirmar_senha}
                        onChange={(e) =>
                          setCadastroForm({
                            ...cadastroForm,
                            confirmar_senha: e.target.value,
                          })
                        }
                        placeholder="Repita sua senha"
                        required
                        className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                      />
                    </label>
                  </div>

                  <label className="flex items-start gap-3 rounded-xl bg-paper p-3.5 ring-1 ring-line">
                    <input
                      type="checkbox"
                      checked={cadastroForm.aceitou_termos}
                      onChange={(e) =>
                        setCadastroForm({
                          ...cadastroForm,
                          aceitou_termos: e.target.checked,
                        })
                      }
                      className="mt-1"
                    />
                    <span className="text-sm leading-relaxed text-mute">
                      Li e aceito os {" "}
                      <button
                        type="button"
                        onClick={() => setDocumentoAberto("termos")}
                        className="font-semibold text-green underline underline-offset-2"
                      >
                        Termos de Uso
                      </button>{" "}
                      e a {" "}
                      <button
                        type="button"
                        onClick={() => setDocumentoAberto("privacidade")}
                        className="font-semibold text-green underline underline-offset-2"
                      >
                        Política de Privacidade
                      </button>.
                    </span>
                  </label>

                  {erroCadastro && (
                    <p className="rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line">
                      {erroCadastro}
                    </p>
                  )}

                  <button
                    type="submit"
                    className="w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white transition-colors duration-200 hover:bg-[#5f8871]"
                  >
                    Criar conta
                  </button>
                </form>
              )}
            </section>

            <div className="mt-6 flex items-center justify-center gap-4 text-xs text-mute">
              <button
                type="button"
                onClick={() => setDocumentoAberto("termos")}
                className="underline underline-offset-2 hover:text-green"
              >
                Termos de Uso
              </button>
              <button
                type="button"
                onClick={() => setDocumentoAberto("privacidade")}
                className="underline underline-offset-2 hover:text-green"
              >
                Política de Privacidade
              </button>
            </div>

            <p className="mt-4 text-center font-hand text-2xl text-mute">
              o caderno da sala de aula
            </p>
          </div>
        </div>

        <ModalDocumento
          tipo={documentoAberto}
          fechar={() => setDocumentoAberto(null)}
        />
      </main>
    );
  }

  return (

    <main className="min-h-screen bg-paper font-sans text-ink antialiased">

      <div className="mx-auto max-w-2xl px-5 py-12 sm:py-16">

        <header className="mb-10 animate-[rise_.6s_cubic-bezier(.32,.72,0,1)_both]">

          <div className="flex items-center gap-3">

            <span className="grid size-11 place-items-center rounded-2xl bg-card ring-1 ring-line">

              <span className="font-hand text-2xl leading-none text-green">Ag</span>

            </span>

            <div>

              <h1 className="text-2xl font-bold leading-tight">

                Agenda Pedagógica

              </h1>

              <p className="text-sm text-mute">

                Controle de recursos · cadastro de atividades

              </p>

            </div>

          </div>

          <p className="mt-4 font-hand text-3xl leading-tight text-green">

            o caderno da sala de aula

          </p>

          <div className="mt-5 flex items-center justify-between rounded-2xl bg-card px-4 py-3 ring-1 ring-line">
            <div>
              <p className="text-sm font-semibold">{usuario.nome}</p>
              <p className="text-xs capitalize text-mute">{usuario.perfil}</p>
            </div>

            <div className="flex gap-2">
              {usuario.perfil === "coordenador" && (
                <button
                  type="button"
                  onClick={abrirLogs}
                  className="rounded-lg bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line transition-colors hover:bg-card"
                >
                  Logs de auditoria
                </button>
              )}

              <button
                type="button"
                onClick={abrirMeusDados}
                className="rounded-lg bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line transition-colors hover:bg-card"
              >
                Meus dados
              </button>

              <button
                type="button"
                onClick={fazerLogout}
                className="rounded-lg bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line transition-colors hover:bg-card"
              >
                Sair
              </button>
            </div>
          </div>

        </header>



        <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8 animate-[rise_.6s_cubic-bezier(.32,.72,0,1)_120ms_both]">

          <div className="mb-6 flex items-baseline justify-between border-b border-line pb-4">

            <h2 className="text-lg font-semibold">Nova atividade</h2>

            <span className="font-hand text-2xl text-cream">página 01</span>

          </div>

          <form

            onSubmit={handleSubmit}

            className="grid grid-cols-1 gap-4 sm:grid-cols-2"

          >

            <label className="block">

              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                Disciplina

              </span>

              <select

                name="disciplina"

                value={form.disciplina}

                onChange={handleChange}

                required

                className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

              >

                <option value="" disabled>

                  Selecione a disciplina

                </option>

                {disciplinas.map((disciplina) => (

  <option key={disciplina.id} value={disciplina.id}>

    {disciplina.nome}

  </option>

))}

              </select>

            </label>

            <label className="block">

              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                Turma

              </span>

              <select

                name="turma"

                value={form.turma}

                onChange={handleChange}

                required

                className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

              >

                <option value="" disabled>

                  Selecione a turma

                </option>

                {turmas.map((turma) => (

  <option key={turma.id} value={turma.id}>

    {turma.nome}

  </option>

))}

              </select>

            </label>

            <label className="block sm:col-span-2">

              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                Professor

              </span>

              <select

                name="professor"

                value={form.professor}

                onChange={handleChange}

                required

                className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

              >

                <option value="" disabled>

                  Selecione o professor

                </option>

                {professores.map((professor) => (

  <option key={professor.id} value={professor.id}>

    {professor.nome}

  </option>

))}

              </select>

            </label>

            <label className="block">

              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                Data

              </span>

              <input

                type="date"

                name="data"

                value={form.data}

                onChange={handleChange}

                required

                className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

              />

              {consultandoFeriado && (
                <p className="mt-2 text-xs text-mute">
                  Consultando calendario de feriados...
                </p>
              )}

              {!consultandoFeriado && feriado?.feriado && (
                <div className="mt-2 rounded-xl bg-cream/30 px-3 py-2 text-sm ring-1 ring-line">
                  <span className="font-semibold">Atencao:</span>{" "}
                  esta data corresponde ao feriado {feriado.nome}.
                </div>
              )}

            </label>

            <div className="grid grid-cols-2 gap-3">

              <label className="block">

                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                  Início

                </span>

                <input

                  type="time"

                  name="horarioInicial"

                  value={form.horarioInicial}

                  onChange={handleChange}

                  required

                  className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

                />

              </label>

              <label className="block">

                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                  Fim

                </span>

                <input

                  type="time"

                  name="horarioFinal"

                  value={form.horarioFinal}

                  onChange={handleChange}

                  required

                  className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"

                />

              </label>

            </div>

            <label className="block sm:col-span-2">

              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-mute">

                Descrição

              </span>

              <textarea

                name="descricao"

                value={form.descricao}

                onChange={handleChange}

                rows={3}

                placeholder="Aula prática sobre frações no laboratório..."

                required

                className="w-full resize-none rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line placeholder:text-mute/60 focus:outline-none focus:ring-2 focus:ring-green"

              />

            </label>

            <div className="sm:col-span-2">

              <button

                type="submit"

                className="group w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white transition-colors duration-200 hover:bg-[#5f8871]"

              >

                Adicionar atividade

                <span className="ml-1 inline-block transition-transform duration-200 group-hover:translate-x-0.5">

                  →

                </span>

              </button>

            </div>

          </form>

        </section>

<section className="mt-10 rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8">



  <div className="mb-6">

    <h2 className="text-lg font-semibold">Alocar recurso</h2>

    <p className="mt-1 text-sm text-mute">

      Escolha uma atividade e o recurso que vai ser usado

    </p>

  </div>



  <form onSubmit={salvarAlocacao} className="space-y-4">



    <label className="block">

      <span className="mb-1.5 block text-xs font-semibold uppercase text-mute">

        Atividade

      </span>



      <select

        value={atividadeEscolhida}

        onChange={(e) => setAtividadeEscolhida(e.target.value)}

        className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line"

        required

      >

        <option value="">Selecione uma atividade</option>



        {activities.map((atividade) => (

          <option key={atividade.id} value={atividade.id}>

            {atividade.disciplina} - {atividade.turma} - {atividade.data}

          </option>

        ))}



      </select>

    </label>



    <label className="block">

      <span className="mb-1.5 block text-xs font-semibold uppercase text-mute">

        Recurso

      </span>



      <select

        value={recursoEscolhido}

        onChange={(e) => setRecursoEscolhido(e.target.value)}

        className="w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line"

        required

      >

        <option value="">Selecione um recurso</option>



        {recursos.map((recurso) => (

          <option key={recurso.id} value={recurso.id}>

            {recurso.nome} - {recurso.tipo}

          </option>

        ))}



      </select>

    </label>



    <button

      type="submit"

      className="w-full rounded-xl bg-green px-4 py-3 text-sm font-semibold text-white"

    >

      Alocar recurso

    </button>



  </form>



  <div className="mt-8">

    <h3 className="mb-3 font-semibold">Recursos alocados</h3>

    {alocacoes.length === 0 && (
      <p className="text-sm text-mute">
        Nenhum recurso alocado ainda.
      </p>
    )}

    {alocacoesPagina.map((item) => (
      <div
        key={item.id}
        className="mb-3 rounded-xl bg-paper p-4 ring-1 ring-line"
      >
        <strong>{item.disciplina} - {item.turma}</strong>

        <p className="text-sm text-mute">
          {item.professor}
        </p>

        <p className="mt-1 text-sm">
          Recurso: {item.recurso} ({item.tipo})
        </p>

        <p className="text-sm">
          {item.data} · {item.hora_inicio} até {item.hora_fim}
        </p>

        <div className="mt-4 flex gap-2">

          <button
            type="button"
            onClick={() => {
              setEditandoAlocacao(item.id);
              setNovoRecurso("");
            }}
            className="rounded-lg bg-green px-3 py-2 text-sm font-semibold text-white"
          >
            Alterar
          </button>

          <button
            type="button"
            onClick={() => cancelarAlocacao(item.id)}
            className="rounded-lg bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line"
          >
            Cancelar
          </button>

        </div>

        {editandoAlocacao === item.id && (

          <div className="mt-4">

            <p className="mb-2 text-sm font-semibold">
              Escolha o novo recurso
            </p>

            <select
              value={novoRecurso}
              onChange={(e) => setNovoRecurso(e.target.value)}
              className="w-full rounded-xl bg-card px-3 py-2 text-sm ring-1 ring-line"
            >
              <option value="">
                Selecione um recurso
              </option>

              {recursos.map((recurso) => (
                <option
                  key={recurso.id}
                  value={recurso.id}
                >
                  {recurso.nome} - {recurso.tipo}
                </option>
              ))}
            </select>

            <div className="mt-3 flex gap-2">

              <button
                type="button"
                onClick={() => alterarAlocacao(item.id)}
                className="rounded-lg bg-green px-3 py-2 text-sm font-semibold text-white"
              >
                Salvar
              </button>

              <button
                type="button"
                onClick={() => {
                  setEditandoAlocacao(null);
                  setNovoRecurso("");
                }}
                className="rounded-lg bg-paper px-3 py-2 text-sm ring-1 ring-line"
              >
                Voltar
              </button>

            </div>

          </div>

        )}

      </div>
    ))}

    {totalPaginasAlocacoes > 1 && (

      <div className="mt-5 flex items-center justify-center gap-3">

        <button
          type="button"
          disabled={paginaAlocacoes === 1}
          onClick={() => setPaginaAlocacoes(paginaAlocacoes - 1)}
          className="rounded-lg bg-paper px-3 py-2 text-sm ring-1 ring-line disabled:opacity-40"
        >
          Anterior
        </button>

        <span className="text-sm text-mute">
          Pagina {paginaAlocacoes} de {totalPaginasAlocacoes}
        </span>

        <button
          type="button"
          disabled={paginaAlocacoes === totalPaginasAlocacoes}
          onClick={() => setPaginaAlocacoes(paginaAlocacoes + 1)}
          className="rounded-lg bg-paper px-3 py-2 text-sm ring-1 ring-line disabled:opacity-40"
        >
          Proxima
        </button>

      </div>

    )}

  </div>



</section>

        <section className="mt-12">

          <div className="mb-5 flex items-baseline justify-between">

            <h2 className="text-lg font-semibold">Atividades cadastradas</h2>

            <span className="text-sm text-mute">
              {activities.length} registrada{activities.length !== 1 ? "s" : ""}
            </span>

          </div>

          <div className="space-y-4">

            {atividadesPagina.map((activity, index) => (

              <article
                key={activity.id}
                className="rounded-[24px] bg-card p-5 ring-1 ring-line [box-shadow:0_18px_40px_-28px_rgba(69,61,46,.4)] transition-transform duration-200 hover:-translate-y-0.5 animate-[pop_.5s_cubic-bezier(.32,.72,0,1)_both]"
                style={{ animationDelay: `${200 + index * 120}ms` }}
              >

                <div className="flex items-start justify-between gap-4">

                  <div className="min-w-0">

                    <h3 className="truncate text-base font-semibold">
                      {activity.disciplina} — {activity.turma}
                    </h3>

                    <p className="mt-0.5 text-sm text-mute">
                      {activity.professor} · {formatDate(activity.data)} ·{" "}
                      {activity.horarioInicial} – {activity.horarioFinal}
                    </p>

                  </div>

                  <span
                    className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${getBadgeStyle(
                      activity.disciplina
                    )}`}
                  >
                    {activity.disciplina}
                  </span>

                </div>

                <p className="mt-3 text-sm leading-relaxed text-ink/80">
                  {activity.descricao}
                </p>

              </article>

            ))}

          </div>

          {totalPaginasAtividades > 1 && (

            <div className="mt-6 flex items-center justify-center gap-3">

              <button
                type="button"
                disabled={paginaAtividades === 1}
                onClick={() => setPaginaAtividades(paginaAtividades - 1)}
                className="rounded-lg bg-card px-3 py-2 text-sm ring-1 ring-line disabled:opacity-40"
              >
                Anterior
              </button>

              <span className="text-sm text-mute">
                Pagina {paginaAtividades} de {totalPaginasAtividades}
              </span>

              <button
                type="button"
                disabled={paginaAtividades === totalPaginasAtividades}
                onClick={() => setPaginaAtividades(paginaAtividades + 1)}
                className="rounded-lg bg-card px-3 py-2 text-sm ring-1 ring-line disabled:opacity-40"
              >
                Proxima
              </button>

            </div>

          )}

        </section>


        <footer className="mt-14 text-center">

          <div className="mb-3 flex items-center justify-center gap-4 text-xs text-mute">
            <button
              type="button"
              onClick={() => setDocumentoAberto("termos")}
              className="underline underline-offset-2 hover:text-green"
            >
              Termos de Uso
            </button>

            <button
              type="button"
              onClick={() => setDocumentoAberto("privacidade")}
              className="underline underline-offset-2 hover:text-green"
            >
              Política de Privacidade
            </button>
          </div>

          <p className="font-hand text-2xl text-mute">até a próxima aula</p>

        </footer>

      </div>

      <ModalDocumento
        tipo={documentoAberto}
        fechar={() => setDocumentoAberto(null)}
      />

      {logsAberto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8">

            <div className="mb-5 flex items-start justify-between gap-4 border-b border-line pb-4">
              <div>
                <h2 className="text-xl font-bold">Logs de auditoria</h2>
                <p className="mt-1 text-sm text-mute">
                  Registro das ações realizadas no sistema
                </p>
              </div>

              <button
                type="button"
                onClick={() => setLogsAberto(false)}
                className="rounded-xl bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line"
              >
                Fechar
              </button>
            </div>

            {carregandoLogs ? (
              <p className="text-sm text-mute">Carregando logs...</p>
            ) : logs.length === 0 ? (
              <p className="text-sm text-mute">Nenhum log encontrado.</p>
            ) : (
              <div className="space-y-3">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="rounded-xl bg-paper p-4 ring-1 ring-line"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold">{log.acao}</p>

                      <p className="text-xs text-mute">
                        {log.data_hora}
                      </p>
                    </div>

                    <p className="mt-2 text-sm">
                      Usuario: {log.usuario || "Usuario removido"}
                    </p>

                    {log.detalhes && (
                      <p className="mt-1 text-sm text-mute">
                        {log.detalhes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

          </div>
        </div>
      )}

      {meusDadosAberto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4">
          <div className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8">
            <div className="mb-5 flex items-start justify-between gap-4 border-b border-line pb-4">
              <div>
                <h2 className="text-xl font-bold">Meus dados</h2>
                <p className="mt-1 text-sm text-mute">Informacoes da sua conta</p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setMeusDadosAberto(false);
                  setSenhaExclusao("");
                  setErroExclusao("");
                }}
                className="rounded-xl bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line"
              >
                Fechar
              </button>
            </div>

            {carregandoDados ? (
              <p className="text-sm text-mute">Carregando...</p>
            ) : meusDados ? (
              <div className="space-y-5">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl bg-paper p-4 ring-1 ring-line">
                    <p className="text-xs font-semibold uppercase text-mute">Nome</p>
                    <p className="mt-1 text-sm font-semibold">{meusDados.nome}</p>
                  </div>

                  <div className="rounded-xl bg-paper p-4 ring-1 ring-line">
                    <p className="text-xs font-semibold uppercase text-mute">Perfil</p>
                    <p className="mt-1 text-sm font-semibold capitalize">{meusDados.perfil}</p>
                  </div>

                  <div className="rounded-xl bg-paper p-4 ring-1 ring-line sm:col-span-2">
                    <p className="text-xs font-semibold uppercase text-mute">E-mail</p>
                    <p className="mt-1 break-all text-sm font-semibold">{meusDados.email}</p>
                  </div>

                  <div className="rounded-xl bg-paper p-4 ring-1 ring-line">
                    <p className="text-xs font-semibold uppercase text-mute">Identificador institucional</p>
                    <p className="mt-1 text-sm font-semibold">
                      {meusDados.identificador_institucional || "Nao informado"}
                    </p>
                  </div>

                  <div className="rounded-xl bg-paper p-4 ring-1 ring-line">
                    <p className="text-xs font-semibold uppercase text-mute">Aceite dos termos</p>
                    <p className="mt-1 text-sm font-semibold">
                      {meusDados.aceitou_termos ? "Aceito" : "Nao registrado"}
                    </p>
                    {meusDados.data_aceite && (
                      <p className="mt-1 text-xs text-mute">{meusDados.data_aceite}</p>
                    )}
                  </div>
                </div>

                <div className="rounded-xl bg-paper p-4 text-sm leading-relaxed ring-1 ring-line">
                  <p className="font-semibold">Privacidade</p>
                  <p className="mt-1 text-mute">
                    Voce pode consultar estes dados sempre que precisar. Ao excluir a conta,
                    o vinculo da conta com atividades anteriores e removido. Registros de auditoria
                    podem ser preservados sem o vinculo direto com a conta.
                  </p>
                </div>

                {meusDados.perfil === "coordenador" ? (
                  <div className="rounded-xl bg-paper p-4 text-sm ring-1 ring-line">
                    A conta de coordenador nao pode ser excluida por esta opcao administrativa.
                  </div>
                ) : (
                  <div className="rounded-xl p-4 ring-1 ring-line">
                    <h3 className="font-semibold">Excluir minha conta</h3>
                    <p className="mt-1 text-sm text-mute">
                      Para confirmar a exclusao, digite sua senha. Essa acao nao pode ser desfeita.
                    </p>

                    <input
                      type="password"
                      value={senhaExclusao}
                      onChange={(e) => setSenhaExclusao(e.target.value)}
                      placeholder="Digite sua senha"
                      className="mt-4 w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
                    />

                    {erroExclusao && (
                      <p className="mt-3 text-sm font-semibold text-ink">{erroExclusao}</p>
                    )}

                    <button
                      type="button"
                      onClick={excluirMinhaConta}
                      className="mt-4 w-full rounded-xl bg-paper px-4 py-3 text-sm font-semibold ring-1 ring-line transition-colors hover:bg-card"
                    >
                      Excluir minha conta
                    </button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}

    </main>

  );

}

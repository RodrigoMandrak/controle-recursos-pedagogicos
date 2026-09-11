import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";

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

function Index() {
  const [activities, setActivities] = useState([]);
  const [disciplinas, setDisciplinas] = useState([]);
const [turmas, setTurmas] = useState([]);
const [professores, setProfessores] = useState([]);
  const [form, setForm] = useState({
    disciplina: "",
    turma: "",
    professor: "",
    data: "",
    horarioInicial: "",
    horarioFinal: "",
    descricao: "",
  });
async function carregarAtividades() {
  try {
    const resposta = await fetch("http://127.0.0.1:5000/atividades");
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
    const respostaDisciplinas = await fetch("http://127.0.0.1:5000/disciplinas");
    const dadosDisciplinas = await respostaDisciplinas.json();
    setDisciplinas(dadosDisciplinas);

    const respostaTurmas = await fetch("http://127.0.0.1:5000/turmas");
    const dadosTurmas = await respostaTurmas.json();
    setTurmas(dadosTurmas);

    const respostaProfessores = await fetch("http://127.0.0.1:5000/professores");
    const dadosProfessores = await respostaProfessores.json();
    setProfessores(dadosProfessores);

  } catch (erro) {
    console.log("Erro ao carregar dados", erro);
  }
}

useEffect(() => {
  carregarAtividades();
  carregarOpcoes();
}, []);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
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
    const resposta = await fetch("http://127.0.0.1:5000/atividades", {
      method: "POST",
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
    setForm({
      disciplina: "",
      turma: "",
      professor: "",
      data: "",
      horarioInicial: "",
      horarioFinal: "",
      descricao: "",
    });

  } catch (erro) {
    alert("Erro ao conectar com o servidor");
    console.log(erro);
  }
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

        <section className="mt-12">
          <div className="mb-5 flex items-baseline justify-between">
            <h2 className="text-lg font-semibold">Atividades cadastradas</h2>
            <span className="text-sm text-mute">
              {activities.length} registrada{activities.length !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-4">
            {activities.map((activity, index) => (
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
        </section>

        <footer className="mt-14 text-center">
          <p className="font-hand text-2xl text-mute">até a próxima aula</p>
        </footer>
      </div>
    </main>
  );
}

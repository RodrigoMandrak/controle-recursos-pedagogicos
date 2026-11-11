import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LabelList,
} from "recharts";

// cores do tema "caderno" (mesmas do styles.css)
const CORES = {
  verde: "#6f9780",
  azul: "#7296ad",
  creme: "#eddcb4",
  tinta: "#453d2e",
  mute: "#8b8069",
  linha: "#e6dcc4",
  papel: "#f4efe1",
};

const CORES_DISCIPLINA = ["#6f9780", "#7296ad", "#c9a86a", "#b5654f", "#8b8069"];

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

// no eixo do grafico aparece so o mes ("nov"), para os nomes nao se encostarem
function formatarMes(mesTexto) {
  const mes = Number(mesTexto.split("-")[1]);
  return MESES[mes - 1];
}

// no subtitulo aparece o periodo com o ano ("jul/26 a dez/26")
function formatarMesAno(mesTexto) {
  const [ano, mes] = mesTexto.split("-").map(Number);
  return `${MESES[mes - 1]}/${String(ano).slice(2)}`;
}

function CardNumero({ titulo, valor, detalhe, destaque }) {
  return (
    <div
      className={
        destaque
          ? "rounded-2xl bg-[#4f7a63] p-5 text-white [box-shadow:0_18px_40px_-28px_rgba(47,74,60,.7)]"
          : "rounded-2xl bg-card p-5 ring-1 ring-line [box-shadow:0_18px_40px_-30px_rgba(69,61,46,.4)]"
      }
    >
      <p
        className={`text-xs font-semibold uppercase tracking-wide ${
          destaque ? "text-white/80" : "text-mute"
        }`}
      >
        {titulo}
      </p>
      <p className="mt-2 text-4xl font-bold tabular-nums">{valor}</p>
      <p className={`text-xs ${destaque ? "text-white/80" : "text-mute"}`}>
        {detalhe}
      </p>
    </div>
  );
}

function Painel({ titulo, subtitulo, children }) {
  return (
    <div className="rounded-[24px] bg-card p-6 ring-1 ring-line [box-shadow:0_18px_40px_-30px_rgba(69,61,46,.4)]">
      <h3 className="font-semibold">{titulo}</h3>
      <p className="mb-4 text-sm text-mute">{subtitulo}</p>
      {children}
    </div>
  );
}

function SemDados({ texto }) {
  return (
    <div className="grid h-[220px] place-items-center rounded-xl bg-paper text-sm text-mute ring-1 ring-line">
      {texto}
    </div>
  );
}

// filtro vazio = dashboard completo (igual era antes)
const FILTRO_VAZIO = { inicio: "", fim: "", disciplina: "" };

// monta o "?inicio=...&fim=...&disciplina=..." so com os campos preenchidos
function montarConsulta(filtro) {
  const parametros = new URLSearchParams();
  if (filtro.inicio) parametros.set("inicio", filtro.inicio);
  if (filtro.fim) parametros.set("fim", filtro.fim);
  if (filtro.disciplina) parametros.set("disciplina", filtro.disciplina);
  const texto = parametros.toString();
  return texto ? `?${texto}` : "";
}

// "2026-09-01" -> "01/09/2026"
function formatarData(texto) {
  const [ano, mes, dia] = texto.split("-");
  return `${dia}/${mes}/${ano}`;
}

function Dashboard({ api, perfil, versao }) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  // filtro: o que esta digitado nos campos e o que ja foi aplicado no painel
  const [disciplinas, setDisciplinas] = useState([]);
  const [campos, setCampos] = useState(FILTRO_VAZIO);
  const [filtro, setFiltro] = useState(FILTRO_VAZIO);
  const [erroFiltro, setErroFiltro] = useState("");

  // lista de disciplinas para o select do filtro
  useEffect(() => {
    fetch(`${api}/disciplinas`, { credentials: "include" })
      .then((resposta) => (resposta.ok ? resposta.json() : []))
      .then((lista) => setDisciplinas(Array.isArray(lista) ? lista : []))
      .catch(() => setDisciplinas([]));
  }, [api]);

  useEffect(() => {
    async function carregar() {
      try {
        setErro("");
        const resposta = await fetch(`${api}/dashboard${montarConsulta(filtro)}`, {
          credentials: "include",
        });
        const resultado = await resposta.json();

        if (!resposta.ok) {
          // erro no filtro: mantem o painel na tela e mostra o aviso embaixo do filtro
          if (resposta.status === 400) {
            setErroFiltro(resultado.erro || "Filtro inválido.");
            return;
          }
          setErro(resultado.erro || "Não foi possível carregar o dashboard.");
          return;
        }

        setErroFiltro("");
        setDados(resultado);
      } catch {
        setErro("Não foi possível conectar com o servidor para carregar o dashboard.");
      } finally {
        setCarregando(false);
      }
    }

    carregar();
  }, [api, versao, filtro]);

  function aplicarFiltro(e) {
    e.preventDefault();

    // mesma regra do back-end, conferida antes de mandar
    if (campos.inicio && campos.fim && campos.fim < campos.inicio) {
      setErroFiltro("A data final precisa ser depois da data inicial.");
      return;
    }

    setErroFiltro("");
    setFiltro({ ...campos });
  }

  function limparFiltro() {
    setCampos(FILTRO_VAZIO);
    setFiltro(FILTRO_VAZIO);
    setErroFiltro("");
  }

  const temFiltro = Boolean(filtro.inicio || filtro.fim || filtro.disciplina);
  const nomeDisciplina =
    disciplinas.find((item) => String(item.id) === String(filtro.disciplina))?.nome || "";

  const ehCoordenador = perfil === "coordenador";

  if (carregando) {
    return (
      <section className="mb-10 rounded-[28px] bg-card p-6 text-sm text-mute ring-1 ring-line">
        Carregando dashboard...
      </section>
    );
  }

  if (erro) {
    return (
      <section className="mb-10 rounded-[28px] bg-card p-6 ring-1 ring-line">
        <p className="text-sm font-semibold">{erro}</p>
      </section>
    );
  }

  const ind = dados.indicadores;

  const hoje = new Date();
  const mesAtual = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;

  const porMes = dados.por_mes.map((item) => ({
    mes: formatarMes(item.mes),
    mesAno: formatarMesAno(item.mes),
    total: item.total,
    atual: item.mes === mesAtual,
  }));

  const temPorMes = porMes.some((item) => item.total > 0);

  const periodo = dados.por_mes.length
    ? `${formatarMesAno(dados.por_mes[0].mes)} a ${formatarMesAno(dados.por_mes[dados.por_mes.length - 1].mes)}`
    : "";

  return (
    <section className="mb-10 space-y-5 animate-[rise_.6s_cubic-bezier(.32,.72,0,1)_60ms_both]">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">
          {ehCoordenador ? "Visão geral da instituição" : "Meu resumo"}
        </h2>
        <span className="font-hand text-2xl text-green">dashboard</span>
      </div>

      <form
        onSubmit={aplicarFiltro}
        className="rounded-2xl bg-card p-5 ring-1 ring-line [box-shadow:0_18px_40px_-30px_rgba(69,61,46,.4)]"
        aria-label="Filtro do dashboard"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-mute">
            De
            <input
              type="date"
              value={campos.inicio}
              onChange={(e) => setCampos({ ...campos, inicio: e.target.value })}
              className="mt-1 w-full rounded-xl bg-paper px-3 py-2 text-sm font-normal normal-case tracking-normal text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
            />
          </label>
          <label className="text-xs font-semibold uppercase tracking-wide text-mute">
            Até
            <input
              type="date"
              value={campos.fim}
              onChange={(e) => setCampos({ ...campos, fim: e.target.value })}
              className="mt-1 w-full rounded-xl bg-paper px-3 py-2 text-sm font-normal normal-case tracking-normal text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
            />
          </label>
          <label className="text-xs font-semibold uppercase tracking-wide text-mute">
            Disciplina
            <select
              value={campos.disciplina}
              onChange={(e) => setCampos({ ...campos, disciplina: e.target.value })}
              className="mt-1 w-full rounded-xl bg-paper px-3 py-2 text-sm font-normal normal-case tracking-normal text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
            >
              <option value="">Todas</option>
              {disciplinas.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-mute">
            {temFiltro
              ? `Filtrando: ${filtro.inicio ? `de ${formatarData(filtro.inicio)} ` : ""}${
                  filtro.fim ? `até ${formatarData(filtro.fim)} ` : ""
                }${nomeDisciplina ? `· ${nomeDisciplina}` : ""}`
              : "Sem filtro: mostrando tudo"}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={limparFiltro}
              className="rounded-lg bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line transition-colors hover:bg-card"
            >
              Limpar
            </button>
            <button
              type="submit"
              className="rounded-lg bg-[#4f7a63] px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#3f6550]"
            >
              Filtrar
            </button>
          </div>
        </div>

        {erroFiltro && (
          <p className="mt-3 rounded-xl bg-paper px-3 py-2 text-sm font-semibold text-[#8f3f2c] ring-1 ring-line">
            {erroFiltro}
          </p>
        )}
      </form>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <CardNumero
          destaque
          titulo="Atividades hoje"
          valor={ind.atividades_hoje}
          detalhe={ehCoordenador ? "em toda a instituição" : "cadastradas por você"}
        />
        <CardNumero
          titulo="Atividades"
          valor={ind.total_atividades}
          detalhe={temFiltro ? "no filtro escolhido" : "cadastradas no total"}
        />
        <CardNumero
          titulo="Recursos alocados"
          valor={ind.total_alocacoes}
          detalhe={`${ind.sem_recurso} atividade${ind.sem_recurso !== 1 ? "s" : ""} sem recurso`}
        />
        <CardNumero
          titulo="Recursos em uso"
          valor={`${ind.recursos_usados} de ${ind.total_recursos}`}
          detalhe="já reservados ao menos uma vez"
        />
      </div>

      <Painel
        titulo="Atividades por mês"
        subtitulo={`Atividades cadastradas de ${periodo} · o mês atual aparece em verde`}
      >
        {!temPorMes ? (
          <SemDados texto="Nenhuma atividade nesse período." />
        ) : (
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={porMes} margin={{ top: 22, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke={CORES.linha} />
              <XAxis
                dataKey="mes"
                interval={0}
                tick={{ fill: CORES.mute, fontSize: 13 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: CORES.mute, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: CORES.papel }}
                labelFormatter={(_, itens) => itens?.[0]?.payload?.mesAno ?? ""}
                formatter={(valor) => [valor, "Atividades"]}
              />
              <Bar dataKey="total" radius={[8, 8, 0, 0]} maxBarSize={56}>
                {porMes.map((item) => (
                  <Cell key={item.mesAno} fill={item.atual ? CORES.verde : CORES.azul} />
                ))}
                <LabelList
                  dataKey="total"
                  position="top"
                  style={{ fill: CORES.tinta, fontSize: 13, fontWeight: 600 }}
                  formatter={(valor) => (valor > 0 ? valor : "")}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Painel>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Painel
          titulo="Recursos mais reservados"
          subtitulo="Alocações por recurso"
        >
          {dados.recursos_mais_usados.length === 0 ? (
            <SemDados texto="Nenhum recurso alocado ainda." />
          ) : (
            <ResponsiveContainer width="100%" height={230}>
              <BarChart
                data={dados.recursos_mais_usados}
                layout="vertical"
                margin={{ top: 0, right: 28, left: 0, bottom: 0 }}
              >
                <XAxis type="number" hide allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="recurso"
                  width={100}
                  tick={{ fill: CORES.tinta, fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: CORES.papel }}
                  formatter={(valor) => [valor, "Alocações"]}
                />
                <Bar dataKey="total" fill={CORES.verde} radius={[0, 6, 6, 0]} maxBarSize={20}>
                  <LabelList
                    dataKey="total"
                    position="right"
                    style={{ fill: CORES.tinta, fontSize: 13, fontWeight: 600 }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Painel>

        <Painel
          titulo="Atividades por disciplina"
          subtitulo="Distribuição das atividades"
        >
          {dados.por_disciplina.length === 0 ? (
            <SemDados texto="Nenhuma atividade cadastrada ainda." />
          ) : (
            <div className="space-y-3">
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie
                    data={dados.por_disciplina}
                    dataKey="total"
                    nameKey="disciplina"
                    innerRadius={42}
                    outerRadius={68}
                    paddingAngle={2}
                    stroke="none"
                  >
                    {dados.por_disciplina.map((item, indice) => (
                      <Cell
                        key={item.disciplina}
                        fill={CORES_DISCIPLINA[indice % CORES_DISCIPLINA.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(valor, nome) => [valor, nome]} />
                </PieChart>
              </ResponsiveContainer>

              <ul className="space-y-1.5">
                {dados.por_disciplina.map((item, indice) => (
                  <li
                    key={item.disciplina}
                    className="flex items-center justify-between gap-3 rounded-xl bg-paper px-3 py-1.5 text-sm ring-1 ring-line"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <span
                        className="size-3 shrink-0 rounded-full"
                        style={{
                          background: CORES_DISCIPLINA[indice % CORES_DISCIPLINA.length],
                        }}
                      />
                      <span className="truncate">{item.disciplina}</span>
                    </span>
                    <strong className="tabular-nums">{item.total}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Painel>
      </div>
    </section>
  );
}

export default Dashboard;

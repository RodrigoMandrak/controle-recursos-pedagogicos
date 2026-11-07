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
          ? "rounded-2xl bg-green p-4 text-white"
          : "rounded-2xl bg-card p-4 ring-1 ring-line"
      }
    >
      <p
        className={`text-xs font-semibold uppercase tracking-wide ${
          destaque ? "text-white/80" : "text-mute"
        }`}
      >
        {titulo}
      </p>
      <p className="mt-1 text-3xl font-bold tabular-nums">{valor}</p>
      <p className={`text-xs ${destaque ? "text-white/80" : "text-mute"}`}>
        {detalhe}
      </p>
    </div>
  );
}

function Painel({ titulo, subtitulo, children }) {
  return (
    <div className="rounded-[24px] bg-card p-5 ring-1 ring-line">
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

function Dashboard({ api, perfil, versao }) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    async function carregar() {
      try {
        setErro("");
        const resposta = await fetch(`${api}/dashboard`, {
          credentials: "include",
        });
        const resultado = await resposta.json();

        if (!resposta.ok) {
          setErro(resultado.erro || "Não foi possível carregar o dashboard.");
          return;
        }

        setDados(resultado);
      } catch {
        setErro("Não foi possível conectar com o servidor para carregar o dashboard.");
      } finally {
        setCarregando(false);
      }
    }

    carregar();
  }, [api, versao]);

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

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <CardNumero
          destaque
          titulo="Atividades hoje"
          valor={ind.atividades_hoje}
          detalhe={ehCoordenador ? "em toda a instituição" : "cadastradas por você"}
        />
        <CardNumero
          titulo="Atividades"
          valor={ind.total_atividades}
          detalhe="cadastradas no total"
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

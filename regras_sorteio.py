import random
import json
import streamlit as st

def gerar_sorteio(lista_presenca):
    total_jogadores = len(lista_presenca)
    if total_jogadores < 10:
        return None, "Poucos jogadores confirmados para formar times equilibrados."

    goleiros = [j for j in lista_presenca if j[4] == 'Goleiro']
    linha = [j for j in lista_presenca if j[4] != 'Goleiro']
    num_times = 2 if total_jogadores <= 14 else 3

    goleiros_fixos = False
    if num_times == 3 and len(goleiros) == 2: goleiros_fixos = True
    times = {i: [] for i in range(1, num_times + 1)}

    if not goleiros_fixos:
        random.shuffle(goleiros)
        for idx, gol in enumerate(goleiros):
            time_destino = (idx % num_times) + 1
            times[time_destino].append(gol)

    posicoes_ordem = ['Zagueiro', 'Lateral', 'Meio-campo', 'Atacante', 'Não informada']
    ordem_times_draft = list(range(1, num_times + 1))
    random.shuffle(ordem_times_draft)
    direcao_ida = True
    idx_draft = 0

    for pos in posicoes_ordem:
        jogadores_pos = [j for j in linha if j[4] == pos]
        random.shuffle(jogadores_pos)
        jogadores_pos.sort(key=lambda x: x[3] + random.uniform(-0.5, 0.5), reverse=True)

        for jog in jogadores_pos:
            time_destino = ordem_times_draft[idx_draft]
            times[time_destino].append(jog)
            if direcao_ida:
                idx_draft += 1
                if idx_draft >= num_times:
                    idx_draft = num_times - 1
                    direcao_ida = False
            else:
                idx_draft -= 1
                if idx_draft < 0:
                    idx_draft = 0
                    direcao_ida = True

    times_formatados = {}
    for t_num, elenco in times.items():
        t_gols = [j for j in elenco if j[4] == 'Goleiro']
        t_linha = [j for j in elenco if j[4] != 'Goleiro']

        t_linha.sort(key=lambda x: (0 if x[2] == 'Fixo' else 1, -x[3]))
        times_formatados[f"Time {t_num}"] = {
            "Goleiros": t_gols,
            "Titulares": t_linha[:5],
            "Reservas": t_linha[5:]
        }

    resultado_final = {"times": times_formatados, "goleiros_fixos": goleiros_fixos, "lista_goleiros": goleiros}
    return json.dumps(resultado_final), None

def exibir_times(json_str):
    resultado = json.loads(json_str)
    if resultado['goleiros_fixos']:
        st.warning("⚠️ **Exceção Ativada:** Temos 3 times mas apenas 2 Goleiros. Eles serão fixos na quadra.")
        nomes_gols = ", ".join([g[1] for g in resultado['lista_goleiros']])
        st.markdown(f"**🧤 Goleiros Fixos da Rodada:** {nomes_gols}")

    colunas_times = st.columns(len(resultado['times']))
    for i, (nome_time, elenco) in enumerate(resultado['times'].items()):
        with colunas_times[i]:
            st.markdown(f"### 🛡️ {nome_time}")
            if elenco['Goleiros'] and not resultado['goleiros_fixos']:
                st.markdown(f"**🧤 Goleiro:** {elenco['Goleiros'][0][1]}")
            st.markdown("**Titulares:**")
            for t in elenco['Titulares']: st.write(f"- {t[1]} ({t[4]})")
            if elenco['Reservas']:
                st.markdown("**🔄 Reservas:**")
                for r in elenco['Reservas']: st.write(f"- {r[1]} {'(Convidado)' if r[2] == 'Convidado' else ''}")
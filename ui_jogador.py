import streamlit as st
import sqlite3
import json
from datetime import datetime
import database as db
import regras_sorteio as rs


def render_jogador():
    st.title("⚽ Painel do Jogador")
    st.write(f"Fala, {st.session_state['nome_usuario']}! Pronto para o jogo?")
    st.divider()

    partida_atual = db.obter_partida_ativa()
    lista_aberta_horario = db.verificar_limite_horario(partida_atual[1], partida_atual[3]) if partida_atual else False

    guias_jogador = ["📋 Lista de Presença", "🛡️ Times Sorteados"]
    if partida_atual and partida_atual[4] == 'EM AVALIAÇÃO':
        guias_jogador.append("⭐ Avaliação")

    guias_jogador.append("📊 Estatísticas")
    abas_jogador = st.tabs(guias_jogador)

    if partida_atual:
        data_formatada = datetime.strptime(partida_atual[1], '%Y-%m-%d').strftime('%d/%m/%Y')

        with abas_jogador[0]:  # LISTA
            st.info(f"🏆 Partida: **{data_formatada}** às **{partida_atual[3]}** em **{partida_atual[2]}**")
            conn = sqlite3.connect('pelada.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM presencas WHERE partida_id=? AND jogador_id=?",
                           (partida_atual[0], st.session_state['id_usuario']))
            ja_confirmou = cursor.fetchone()
            conn.close()

            if ja_confirmou:
                st.success("✅ Sua presença está confirmada!")
                if partida_atual[4] == 'ABERTA' and st.button("❌ Desistir / Retirar meu nome"):
                    db.remover_presenca(partida_atual[0], st.session_state['id_usuario']);
                    st.rerun()
            else:
                if partida_atual[4] == 'ABERTA' and lista_aberta_horario:
                    if st.button("✅ CONFIRMAR PRESENÇA", use_container_width=True, type="primary"):
                        if db.confirmar_presenca(partida_atual[0], st.session_state['id_usuario']):
                            st.rerun()
                        else:
                            st.error("A lista já atingiu o limite de 21 jogadores!")
                else:
                    st.error(
                        "🔒 A lista de presença está fechada. (O limite de 1h antes do jogo passou ou a diretoria trancou).")

            st.divider()
            st.subheader("Confirmados")
            confirmados = db.obter_lista_presenca(partida_atual[0])
            if confirmados:
                tabela = [{"Nome": c[1], "Tipo": c[2], "Posição": c[4], "Nota": f"{c[3]} ⭐"} for c in confirmados]
                st.dataframe(tabela, use_container_width=True)
            else:
                st.info("Ninguém confirmou ainda.")

        with abas_jogador[1]:  # TIMES
            if partida_atual[5]:
                st.subheader("Os times já estão definidos!")
                rs.exibir_times(partida_atual[5])
            else:
                st.info("A diretoria ainda não sorteou os times.")

        if partida_atual[4] == 'EM AVALIAÇÃO':
            with abas_jogador[2]:  # AVALIAÇÃO
                st.subheader("📝 Avalie o Desempenho")
                if db.verificar_ja_votou(partida_atual[0], st.session_state['id_usuario']):
                    st.success("✅ Você já enviou suas notas! Aguarde a diretoria encerrar o baba.")
                else:
                    colegas = db.obter_colegas_equipe(partida_atual[0], st.session_state['id_usuario'])
                    if not colegas:
                        st.info("Você não foi sorteado em nenhum time oficial ou é um convidado.")
                    else:
                        st.write("De 1 a 10, como foi o jogo dos seus companheiros de time?")
                        with st.form("form_avaliacoes_jog"):
                            notas = {}
                            for col in colegas:
                                notas[col[0]] = st.slider(f"{col[1]}", 1, 10, 5, key=f"ava_{col[0]}")

                            st.divider()
                            st.write("🏆 Voto de Craque do Baba (Pode ser qualquer um)")
                            todos = db.obter_lista_presenca(partida_atual[0])
                            opcoes_craque = {j[0]: j[1] for j in todos if j[5] != st.session_state['id_usuario']}
                            craque = st.selectbox("Quem jogou mais hoje?", options=opcoes_craque.keys(),
                                                  format_func=lambda x: opcoes_craque[x])

                            if st.form_submit_button("Enviar Avaliações", type="primary"):
                                db.salvar_avaliacoes(partida_atual[0], st.session_state['id_usuario'], notas, craque)
                                st.rerun()
    else:
        with abas_jogador[0]:
            st.write("Nenhuma partida ativa no momento.")

    # ESTATÍSTICAS
    with abas_jogador[-1]:
        st.subheader("👑 Atual Campeão")
        ultimo_campeao = db.obter_ultimo_campeao()

        if ultimo_campeao:
            data_camp, nome_time, json_times = ultimo_campeao
            st.success(
                f"🏆 **ATUAL CAMPEÃO** - Baba do dia {datetime.strptime(data_camp, '%Y-%m-%d').strftime('%d/%m/%Y')}")
            st.markdown(f"### 🛡️ {nome_time}")

            dados_times = json.loads(json_times)
            elenco = dados_times['times'][nome_time]
            jogadores_camp = [t[1] for t in elenco['Titulares']] + [r[1] for r in elenco['Reservas']]
            if elenco['Goleiros'] and not dados_times.get('goleiros_fixos'):
                jogadores_camp.append(elenco['Goleiros'][0][1])

            st.write("🏅 **Elenco Vencedor:** " + ", ".join(jogadores_camp))
        else:
            st.info("Nenhum time campeão registrado ainda.")

        st.divider()
        st.subheader("🔥 Top 5 - Maiores da História")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("### ⚽ Artilheiros")
            top_gols = db.obter_top5_estatistica('gols')
            if top_gols:
                for i, (nome, total) in enumerate(top_gols):
                    st.write(f"**{i + 1}º** {nome} ({total})")
            else:
                st.write("Sem gols ainda.")

        with c2:
            st.markdown("### 👟 Assistências")
            top_ast = db.obter_top5_estatistica('assistencias')
            if top_ast:
                for i, (nome, total) in enumerate(top_ast):
                    st.write(f"**{i + 1}º** {nome} ({total})")
            else:
                st.write("Sem assistências ainda.")

        with c3:
            st.markdown("### 🧱 Baliza Zero")
            top_bz = db.obter_top5_estatistica('baliza_zero')
            if top_bz:
                for i, (nome, total) in enumerate(top_bz):
                    st.write(f"**{i + 1}º** {nome} ({total})")
            else:
                st.write("Sem balizas zeradas ainda.")
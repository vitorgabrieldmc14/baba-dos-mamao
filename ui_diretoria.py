import streamlit as st
import sqlite3
import json
from datetime import datetime
import database as db
import regras_sorteio as rs


def render_diretoria(eh_mestre):
    st.title("👔 Painel da Diretoria")

    guias = ["📅 Gestão", "🔀 Sorteio", "⭐ Avaliação", "📈 Desempenho", "👥 Elenco", "📊 Estatísticas"]
    if eh_mestre: guias.append("👑 Acessos")
    abas = st.tabs(guias)

    partida_atual = db.obter_partida_ativa()
    lista_aberta_horario = db.verificar_limite_horario(partida_atual[1], partida_atual[3]) if partida_atual else False

    with abas[0]:  # GESTÃO
        if not partida_atual:
            st.subheader("Criar Novo Baba")
            col1, col2 = st.columns(2)
            data_baba = col1.date_input("Data da Partida:")
            hora_baba = col2.time_input("Hora:")
            local_baba = st.text_input("Local / Quadra:")
            if st.button("Abrir Lista de Presença", type="primary"):
                db.criar_partida(data_baba, hora_baba.strftime("%H:%M"), local_baba)
                st.rerun()
        else:
            st.success(
                f"🏆 Partida Ativa: **{datetime.strptime(partida_atual[1], '%Y-%m-%d').strftime('%d/%m/%Y')}** às **{partida_atual[3]}**")

            st.divider()
            st.subheader("🙋‍♂️ Minha Presença")
            conn = sqlite3.connect('pelada.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM presencas WHERE partida_id=? AND jogador_id=?",
                           (partida_atual[0], st.session_state['id_usuario']))
            ja_confirmou = cursor.fetchone()
            conn.close()

            if ja_confirmou:
                st.success("✅ Sua presença está confirmada nesta pelada!")
                if partida_atual[4] == 'ABERTA' and st.button("❌ Desistir / Retirar meu nome"):
                    db.remover_presenca(partida_atual[0], st.session_state['id_usuario'])
                    st.rerun()
            else:
                if partida_atual[4] == 'ABERTA' and lista_aberta_horario:
                    if st.button("✅ CONFIRMAR MINHA PRESENÇA", use_container_width=True, type="primary"):
                        if db.confirmar_presenca(partida_atual[0], st.session_state['id_usuario']):
                            st.rerun()
                        else:
                            st.error("A lista já atingiu o limite de 21 jogadores!")
                else:
                    st.error(
                        "🔒 A lista de presença está fechada. (O limite de 1h antes do jogo passou ou a diretoria trancou).")

            st.divider()
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if partida_atual[4] == 'ABERTA':
                    st.info("🟢 Status: ABERTA")
                    if st.button("🔒 Fechar Lista Manualmente"):
                        db.alterar_status_partida(partida_atual[0], 'FECHADA')
                        st.rerun()
                elif partida_atual[4] == 'FECHADA':
                    st.error("🔴 Status: FECHADA")
                    if st.button("🔓 Reabrir Lista"):
                        db.alterar_status_partida(partida_atual[0], 'ABERTA')
                        st.rerun()
                else:
                    st.warning("🟡 Status: EM AVALIAÇÃO")

            with col_s2:
                st.write("Evolução do Baba:")
                if partida_atual[4] in ['ABERTA', 'FECHADA']:
                    if st.button("⏱️ Iniciar Avaliação Pós-Jogo", type="primary"):
                        db.alterar_status_partida(partida_atual[0], 'EM AVALIAÇÃO')
                        st.rerun()
                elif partida_atual[4] == 'EM AVALIAÇÃO':
                    opcoes_times = ["Nenhum / Empate"]
                    if partida_atual[5]:
                        resultado_sorteio = json.loads(partida_atual[5])
                        opcoes_times.extend(list(resultado_sorteio['times'].keys()))

                    st.write("Antes de encerrar, defina o Campeão:")
                    time_campeao_selecionado = st.selectbox("Qual time venceu?", opcoes_times)

                    if st.button("🏁 Encerrar Partida Definitivamente", type="primary"):
                        db.encerrar_partida_definitivamente(partida_atual[0], time_campeao_selecionado)
                        st.success("Baba arquivado! Atualize a página para criar outro.")

            if not lista_aberta_horario and partida_atual[4] == 'ABERTA':
                st.warning(
                    "⚠️ O prazo limite (1h antes do jogo) já se esgotou. A lista de presenças foi bloqueada automaticamente.")

            st.divider()
            st.subheader("📋 Lista de Confirmados")
            confirmados = db.obter_lista_presenca(partida_atual[0])
            if confirmados:
                tabela = [{"Nome": c[1], "Tipo": c[2], "Posição": c[4], "Nota": f"{c[3]} ⭐"} for c in confirmados]
                st.dataframe(tabela, use_container_width=True)
                st.write(f"**Total:** {len(confirmados)} / 21 jogadores")

                convidados_lista = [c for c in confirmados if c[2] == 'Convidado']
                if convidados_lista and partida_atual[4] in ['ABERTA', 'FECHADA']:
                    st.write("Remover Convidados:")
                    opcoes_convidados = {c[0]: f"{c[1]} ({c[4]})" for c in convidados_lista}
                    conv_selecionado = st.selectbox("Selecione para remover:", options=opcoes_convidados.keys(),
                                                    format_func=lambda x: opcoes_convidados[x])
                    if st.button("🗑️ Remover Convidado"):
                        db.remover_convidado_bd(conv_selecionado)
                        st.rerun()
            else:
                st.info("Ninguém confirmou ainda.")

            if partida_atual[4] == 'ABERTA':
                st.divider()
                st.subheader("➕ Adicionar Convidado Avulso")
                c1, c2, c3 = st.columns(3)
                n_conv = c1.text_input("Nome:")
                p_conv = c2.selectbox("Posição:", ["Goleiro", "Zagueiro", "Lateral", "Meio-campo", "Atacante"])
                nota_conv = c3.number_input("Nota (1 a 10):", 1, 10, 5)
                if st.button("Inserir Convidado"):
                    if n_conv:
                        if db.adicionar_convidado(partida_atual[0], n_conv, nota_conv, p_conv):
                            st.rerun()
                        else:
                            st.error("A lista já está lotada!")

    with abas[1]:  # SORTEIO
        st.subheader("🔀 Gerador de Times")
        if partida_atual:
            lista_jogadores = db.obter_lista_presenca(partida_atual[0])
            if partida_atual[5]:
                st.success("✅ Sorteio Oficializado!")
                rs.exibir_times(partida_atual[5])
                st.divider()
                if st.button("🔄 Anular Sorteio e Refazer"):
                    db.salvar_sorteio_oficial(partida_atual[0], None)
                    if 'sorteio_temp' in st.session_state: del st.session_state['sorteio_temp']
                    st.rerun()
            else:
                if 'sorteio_temp' in st.session_state:
                    st.warning("👀 PRÉ-VISUALIZAÇÃO (Jogadores ainda não veem isso)")
                    rs.exibir_times(st.session_state['sorteio_temp'])
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ CONFIRMAR SORTEIO OFICIAL", type="primary", use_container_width=True):
                            db.salvar_sorteio_oficial(partida_atual[0], st.session_state['sorteio_temp'])
                            del st.session_state['sorteio_temp']
                            st.rerun()
                    with col2:
                        if st.button("🔀 Misturar Novamente", use_container_width=True):
                            json_str, err = rs.gerar_sorteio(lista_jogadores)
                            if not err: st.session_state['sorteio_temp'] = json_str; st.rerun()
                else:
                    if st.button("⚽ Gerar Sorteio (Rascunho)", type="primary", use_container_width=True):
                        json_str, err = rs.gerar_sorteio(lista_jogadores)
                        if not err:
                            st.session_state['sorteio_temp'] = json_str;
                            st.rerun()
                        else:
                            st.error(err)
        else:
            st.write("Crie uma partida primeiro.")

    with abas[2]:  # AVALIAÇÃO
        st.subheader("📝 Avalie o Desempenho")
        if partida_atual and partida_atual[4] == 'EM AVALIAÇÃO':
            if db.verificar_ja_votou(partida_atual[0], st.session_state['id_usuario']):
                st.success("✅ Você já enviou suas notas! Aguarde o encerramento do baba.")
            else:
                colegas = db.obter_colegas_equipe(partida_atual[0], st.session_state['id_usuario'])
                if not colegas:
                    st.info("Você não foi sorteado em nenhum time oficial ou é um convidado.")
                else:
                    st.write("De 1 a 10, como foi o jogo dos seus companheiros de time?")
                    with st.form("form_avaliacoes_dir"):
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
            st.info("A Avaliação só é liberada quando o status da partida mudar para 'EM AVALIAÇÃO'.")

    with abas[3]:  # DESEMPENHO
        st.subheader("⚽ Lançar Gols, Assistências e Baliza Zero")
        if partida_atual and partida_atual[4] == 'EM AVALIAÇÃO':
            st.write("Digite os números do jogo e clique no botão Salvar lá embaixo.")
            confirmados = db.obter_lista_presenca(partida_atual[0])
            with st.form("form_estatisticas"):
                novos_dados = {}
                for c in confirmados:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    posicao_texto = str(c[4]).upper() if c[4] else ""
                    posicao_abrev = posicao_texto[:3] if posicao_texto else "N/A"
                    col1.write(f"**{c[1]}** ({posicao_abrev})")

                    g_val = int(c[6]) if c[6] else 0
                    a_val = int(c[7]) if c[7] else 0
                    bz_val = int(c[8]) if c[8] else 0

                    g = col2.number_input("Gols", 0, 50, g_val, key=f"g_{c[0]}")
                    a = col3.number_input("Assist", 0, 50, a_val, key=f"a_{c[0]}")
                    bz = col4.number_input("B. Zero", 0, 50, bz_val, key=f"bz_{c[0]}")

                    novos_dados[c[0]] = (g, a, bz)

                if st.form_submit_button("💾 Salvar Estatísticas do Baba", use_container_width=True):
                    conn = sqlite3.connect('pelada.db')
                    cur = conn.cursor()
                    for p_id, (g, a, bz) in novos_dados.items():
                        cur.execute("UPDATE presencas SET gols=?, assistencias=?, baliza_zero=? WHERE id=?",
                                    (int(g), int(a), int(bz), p_id))
                    conn.commit()
                    conn.close()
                    st.success("Estatísticas salvas no banco!")
                    st.rerun()
        else:
            st.info("O Painel de Desempenho só é liberado quando o status da partida mudar para 'EM AVALIAÇÃO'.")

    with abas[4]:  # ELENCO
        st.subheader("👥 Jogadores Cadastrados")
        conn = sqlite3.connect('pelada.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, nota_media, posicao FROM jogadores")
        lista_toda = cursor.fetchall()
        conn.close()

        if lista_toda:
            tabela = [{"ID": j[0], "Nome": j[1], "Posição": j[3], "Nota Geral": f"{j[2]:.1f} ⭐"} for j in lista_toda]
            st.dataframe(tabela, use_container_width=True)

            st.divider()
            st.subheader("✏️ Alterar Nota Manualmente")
            st.write(
                "Ajuste a nota inicial de um jogador. (Após jogar e ser avaliado, o sistema puxará automaticamente a média das últimas 5 partidas).")

            col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
            opcoes_jogadores = {j[0]: f"{j[1]} ({j[2]:.1f} ⭐)" for j in lista_toda}

            jog_selecionado = col_e1.selectbox("Selecione o Jogador:", options=opcoes_jogadores.keys(),
                                               format_func=lambda x: opcoes_jogadores[x])

            nota_atual = next(j[2] for j in lista_toda if j[0] == jog_selecionado)
            nova_nota = col_e2.number_input("Nova Nota", min_value=1.0, max_value=10.0, value=float(nota_atual),
                                            step=0.1)

            if col_e3.button("Atualizar Nota", use_container_width=True):
                db.atualizar_nota_jogador(jog_selecionado, round(nova_nota, 1))
                st.success("Nota atualizada! A mudança já vale para o próximo sorteio.")
                st.rerun()
        else:
            st.info("Nenhum jogador cadastrado ainda.")

    with abas[5]:  # ESTATÍSTICAS
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

    if eh_mestre:
        with abas[6]:  # ACESSOS
            st.subheader("Gerenciar Jogadores")
            conn = sqlite3.connect('pelada.db')
            cur = conn.cursor()
            cur.execute("SELECT id, nome, perfil FROM jogadores")
            todos = cur.fetchall()
            conn.close()
            if len(todos) > 1:
                opcoes = {j[0]: f"{j[1]} ({j[2]})" for j in todos if j[0] != st.session_state['id_usuario']}
                sel = st.selectbox("Selecione:", options=opcoes.keys(), format_func=lambda x: opcoes[x])
                c1, c2 = st.columns(2)
                with c1:
                    n_cargo = st.radio("Perfil:", ["JOGADOR", "DIRETORIA"], horizontal=True)
                    if st.button("Salvar Permissão"): db.alterar_perfil(sel, n_cargo); st.rerun()
                with c2:
                    if st.button("🗑️ Excluir Jogador", type="primary"): db.excluir_jogador(sel); st.rerun()
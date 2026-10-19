import streamlit as st
import database as db


def render_login():
    menu = st.sidebar.selectbox("Acesso", ["Login", "Cadastrar-se"])
    if menu == "Cadastrar-se":
        st.title("📝 Cadastro de Jogador")
        nome = st.text_input("Nome do Jogador:")
        whats_digitado = st.text_input("WhatsApp (11 números, com DDD):", max_chars=11)
        whats_formatado = db.formatar_whatsapp(whats_digitado)
        if len(whats_digitado) > 0: st.caption(f"Número: **{whats_formatado}**")
        senha = st.text_input("Senha:", type="password")
        posicao = st.selectbox("Posição:", ["Goleiro", "Zagueiro", "Lateral", "Meio-campo", "Atacante"])

        # --- NOVAS LISTAS DE CARACTERÍSTICAS (20 CADA) ---
        lista_fortes = [
            "1. Finalização precisa / Matador",
            "2. Passe excelente / Maestro",
            "3. Velocidade / Arranque rápido",
            "4. Fôlego incansável (Motorzinho)",
            "5. Marcação implacável / Carrapato",
            "6. Força física / Ganha no corpo",
            "7. Faz muito bem o Pivô",
            "8. Drible / Habilidade no 1x1",
            "9. Visão de jogo (Lê bem as jogadas)",
            "10. Ótimo posicionamento tático",
            "11. Jogo aéreo / Bom cabeceio",
            "12. Raça / Muita disposição",
            "13. Chute forte de fora da área",
            "14. Boa armação e criatividade",
            "15. Desarme / Bote certeiro",
            "16. Domínio e controle de bola perfeito",
            "17. Joga para o time (Solidário)",
            "18. Liderança em quadra / Orienta o time",
            "19. Especialista em bola parada",
            "20. Reflexos rápidos (Ideal para Goleiros)"
        ]

        lista_fracos = [
            "1. Finalização ruim / Perde muitos gols",
            "2. Erra muitos passes",
            "3. Lento / Falta arranque",
            "4. Cansa muito rápido (Fôlego curto)",
            "5. Marcação frouxa / Dá muito espaço",
            "6. Fraco fisicamente / Perde divididas",
            "7. Ruim de Pivô / Não segura a bola",
            "8. Sem drible / Dificuldade no 1x1",
            "9. Visão de jogo limitada (Joga de cabeça baixa)",
            "10. Vive fora de posição / Desorganizado",
            "11. Ruim pelo alto / Cabeceio fraco",
            "12. Tira o pé na dividida (Falta raça)",
            "13. Chute fraco / Não chuta de longe",
            "14. Pouca criatividade",
            "15. Bote errado / Comete muitas faltas",
            "16. Domínio ruim / A bola 'queima'",
            "17. Fominha / Prende demais a bola",
            "18. Calado / Não se comunica em quadra",
            "19. Inofensivo na bola parada",
            "20. Reflexos lentos"
        ]

        pontos_fortes = st.multiselect("Selecione até 3 Pontos FORTES:", lista_fortes, max_selections=3)
        pontos_fracos = st.multiselect("Selecione até 3 Pontos FRACOS:", lista_fracos, max_selections=3)

        if st.button("Finalizar Cadastro"):
            if db.salvar_jogador(nome, whats_formatado, senha, posicao, pontos_fortes, pontos_fracos):
                st.success("Cadastro realizado! Faça Login.")
            else:
                st.error("WhatsApp já cadastrado!")

    elif menu == "Login":
        st.title("⚽ Gestão da Pelada")
        st.subheader("Acesse sua conta")
        login_whats = db.formatar_whatsapp(st.text_input("WhatsApp:", max_chars=11))
        login_senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            usuario = db.verificar_login(login_whats, login_senha)
            if usuario:
                st.session_state['logado'] = True
                st.session_state['id_usuario'] = usuario[0]
                st.session_state['nome_usuario'] = usuario[1]
                st.session_state['perfil_usuario'] = usuario[2]
                st.session_state['whats_usuario'] = usuario[3]
                st.rerun()
            else:
                st.error("Dados incorretos!")
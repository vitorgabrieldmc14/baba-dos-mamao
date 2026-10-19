import streamlit as st
import base64
import database as db
from ui_login import render_login
from ui_diretoria import render_diretoria
from ui_jogador import render_jogador

# --- CONFIGURAÇÃO DO DONO DO APP ---
NUMERO_MESTRE = "+55 77 99701-2424"

# --- INICIALIZAÇÃO ---
st.set_page_config(page_title="Baba dos Mamão", page_icon="⚽", layout="wide")


# --- FUNÇÃO PARA PLANO DE FUNDO (MARCA D'ÁGUA) ---
def adicionar_plano_de_fundo(imagem_path, opacidade=0.15):
    try:
        # Lê a imagem e converte para um formato que o CSS entende (Base64)
        with open(imagem_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        # O nosso fundo do tema escuro é rgb(18, 18, 18).
        # Para a imagem ter 15% de opacidade, a "película" preta por cima precisa ter 85%
        fator_escuridao = 1.0 - opacidade

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(18, 18, 18, {fator_escuridao}), rgba(18, 18, 18, {fator_escuridao})), url("data:image/png;base64,{encoded_string}");
                background-size: 40vmin; /* Mantém o tamanho da imagem proporcional à tela */
                background-position: center; /* Centraliza perfeitamente */
                background-repeat: no-repeat; /* Não deixa a imagem se repetir igual azulejo */
                background-attachment: fixed; /* A imagem fica parada enquanto você rola a tela */
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        pass  # Se ele não achar a imagem, não dá erro na tela


# Aplica a marca d'água chamando a função antes de carregar o resto do app
adicionar_plano_de_fundo("logo.png", opacidade=0.15)

db.iniciar_banco()

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# --- FLUXO PRINCIPAL ---
if not st.session_state['logado']:
    render_login()
else:
    eh_mestre = (st.session_state['whats_usuario'] == NUMERO_MESTRE)

    # --- COLOCANDO O ESCUDO NA BARRA LATERAL ---
    try:
        st.sidebar.image("logo.png", use_container_width=True)
    except:
        pass

    st.sidebar.markdown(f"👤 **{st.session_state['nome_usuario']}**")

    if eh_mestre:
        st.sidebar.success("👑 Acesso Mestre")

    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    if st.session_state['perfil_usuario'] == "DIRETORIA" or eh_mestre:
        render_diretoria(eh_mestre)
    else:
        render_jogador()
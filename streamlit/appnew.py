import sys
from pathlib import Path

import streamlit as st


# =========================================================
# AGENT
# =========================================================

AGENT_DIR = Path.home() / "ai-agent-lab" / "agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.append(str(AGENT_DIR))

from hybrid_agent import ask_hybrid_agent
from agent import ask_agent


# =========================================================
# RAG
# =========================================================

RAG_SCRIPTS_DIR = Path.home() / "ai-agent-lab" / "rag" / "scripts"

if str(RAG_SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(RAG_SCRIPTS_DIR))

from rag_agent import ask_rag


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="AI Agent Lab - UFRGS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CONFIGURAÇÕES
# =========================================================

LOGO_URL = (
    "https://www.inf.ufrgs.br/site/wp-content/uploads/"
    "2017/09/logo-inf-300x172.jpg"
)


# =========================================================
# ESTILO VISUAL
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 38px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 5px;
        }

        .subtitle {
            font-size: 18px;
            text-align: center;
            color: #666666;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 25px;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .info-card {
            padding: 20px;
            border: 1px solid #dddddd;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .status-card {
            padding: 15px;
            border: 1px solid #dddddd;
            border-radius: 10px;
            text-align: center;
        }

        .footer {
            text-align: center;
            color: #777777;
            font-size: 13px;
            margin-top: 40px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.image(LOGO_URL, width=190)

    st.markdown("---")

    st.markdown("### 🤖 AI Agent Lab")

    selected_mode = st.radio(
        "Selecione o módulo",
        [
            "🤖 Agent",
            "📚 RAG",
            "🗄️ NL2SQL"
        ]
    )

    st.markdown("---")

    st.markdown("### Projeto")

    st.write("Mestrado em Cybersecurity")
    #st.write("UFRGS")
    st.write("Prof. Dr. Jéferson Campos Nobre")
    st.write("Disciplina: Gerência de Aplicações em Redes")

    st.markdown("---")

    st.caption("Laboratório de AI Agent e Observabilidade")


# =========================================================
# CABEÇALHO PRINCIPAL
# =========================================================

header_col1, header_col2, header_col3 = st.columns([1, 3, 1])

with header_col2:

    st.image(LOGO_URL, width=220)

    st.markdown(
        '<div class="main-title">Universidade Federal do Rio Grande do Sul</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">AI Agent Laboratory</div>',
        unsafe_allow_html=True
    )


# =========================================================
# INDICADORES DE STATUS
# =========================================================

st.markdown(
    '<div class="section-title">Status do laboratório</div>',
    unsafe_allow_html=True
)

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    st.metric(
        label="AI Agent",
        value="Online"
    )

with status_col2:
    st.metric(
        label="PostgreSQL",
        value="Connected"
    )

with status_col3:
    st.metric(
        label="RAG",
        value="Online"
    )

with status_col4:
    st.metric(
        label="OpenTelemetry",
        value="Connected"
    )


st.markdown("---")


# =========================================================
# AGENT
# =========================================================

if selected_mode == "🤖 Agent":

    st.markdown(
        '<div class="section-title">🤖 AI Agent</div>',
        unsafe_allow_html=True
    )

    st.info(
        "O AI Agent interpreta a pergunta e decide automaticamente "
        "se deve utilizar RAG ou NL2SQL."
    )

    st.markdown(
        """
        **Fluxo atual:**

        Usuário → Streamlit → AI Agent → RAG ou NL2SQL → Resposta
        """
    )

    st.markdown("### Consulta ao AI Agent")

    question = st.text_area(
        "Pergunta",
        placeholder="Digite uma pergunta para o Agent...",
        height=120
    )

    execute_button = st.button(
        "Executar consulta",
        type="primary"
    )

    if execute_button:

        if not question.strip():

            st.warning(
                "Digite uma pergunta antes de executar."
            )

        else:

            try:

                with st.spinner(
                    "O Agent está processando sua pergunta..."
                ):

                    result = ask_hybrid_agent(question)

                st.success(
                    "Consulta executada com sucesso."
                )

                # =========================================
                # RESPOSTA
                # =========================================

                st.markdown("### 💬 Resposta do Agent")

                st.write(
                    result["answer"]
                )

                # =========================================
                # ROTA
                # =========================================

                st.markdown("### 🧭 Rota escolhida")

                if result["route"] == "RAG":

                    st.info("📚 RAG")

                elif result["route"] == "NL2SQL":

                    st.info("🗄️ NL2SQL")

                # =========================================
                # RESULTADO RAG
                # =========================================

                if result["route"] == "RAG":

                    st.markdown(
                        "### 📚 Documentos recuperados"
                    )

                    for chunk in result["results"]:

                        st.markdown(
                            f"**Chunk {chunk[2]} — "
                            f"Similaridade: {chunk[4]:.4f}**"
                        )

                        st.write(
                            chunk[3]
                        )

                        st.markdown("---")

                # =========================================
                # RESULTADO NL2SQL
                # =========================================

                elif result["route"] == "NL2SQL":

                    st.markdown(
                        "### 🧠 SQL gerado pelo Agent"
                    )

                    st.code(
                        result["sql"],
                        language="sql"
                    )

                    st.markdown(
                        "### 🗄️ Resultado do PostgreSQL"
                    )

                    if result["rows"]:

                        result_data = [
                            dict(
                                zip(
                                    result["columns"],
                                    row
                                )
                            )
                            for row in result["rows"]
                        ]

                        st.dataframe(
                            result_data,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "O PostgreSQL não retornou registros."
                        )

            except Exception as e:

                st.error(
                    "Ocorreu um erro durante a execução do Agent."
                )

                st.exception(e)

    else:

        st.caption(
            'Digite uma pergunta e clique em '
            '"Executar consulta" para iniciar o Agent.'
        )


# =========================================================
# RAG
# =========================================================

elif selected_mode == "📚 RAG":

    st.markdown(
        '<div class="section-title">📚 RAG</div>',
        unsafe_allow_html=True
    )

    st.info(
        "O módulo RAG recupera informações dos documentos "
        "armazenados na base vetorial PostgreSQL."
    )

    st.markdown(
        """
        ### Retrieval-Augmented Generation

        ```text
        Pergunta
           ↓
        Embedding
           ↓
        Busca vetorial
           ↓
        PostgreSQL + pgvector
           ↓
        Contexto
           ↓
        LLM
           ↓
        Resposta
        ```
        """
    )

    st.markdown("### Teste rápido do RAG")

    rag_question = st.text_area(
        "Pergunta para os documentos",
        placeholder=(
            "Ex.: O que acontece quando um funcionário "
            "deixa a organização?"
        ),
        height=100,
        key="rag_question"
    )

    rag_button = st.button(
        "Executar RAG",
        type="primary",
        key="rag_button"
    )

    if rag_button:

        if not rag_question.strip():

            st.warning(
                "Digite uma pergunta antes de executar."
            )

        else:

            try:

                with st.spinner(
                    "Executando RAG..."
                ):

                    result = ask_rag(rag_question)

                st.success(
                    "Consulta RAG executada com sucesso."
                )

                st.markdown("### 💬 Resposta")

                st.write(
                    result["answer"]
                )

                st.markdown(
                    "### 📚 Chunks recuperados"
                )

                for chunk in result["results"]:

                    st.markdown(
                        f"**Chunk {chunk[2]} — "
                        f"Similaridade: {chunk[4]:.4f}**"
                    )

                    st.write(
                        chunk[3]
                    )

                    st.markdown("---")

            except Exception as e:

                st.error(
                    "Erro durante a execução do RAG."
                )

                st.exception(e)


# =========================================================
# NL2SQL
# =========================================================

elif selected_mode == "🗄️ NL2SQL":

    st.markdown(
        '<div class="section-title">🗄️ NL2SQL</div>',
        unsafe_allow_html=True
    )

    st.success(
        "O pipeline NL2SQL está funcionando através do AI Agent."
    )

    st.info(
        "O módulo NL2SQL transforma perguntas em linguagem natural "
        "em consultas SQL para o PostgreSQL."
    )

    st.markdown(
        """
        ### Natural Language → SQL

        ```text
        Pergunta
           ↓
        AI Agent
           ↓
        LLM
           ↓
        SQL
           ↓
        PostgreSQL
           ↓
        Resultado
           ↓
        LLM
           ↓
        Resposta
        ```
        """
    )

    st.markdown(
        "### Teste rápido do NL2SQL"
    )

    nl2sql_question = st.text_area(
        "Pergunta para o banco",
        placeholder=(
            "Ex.: Quais clientes fizeram mais pedidos?"
        ),
        height=100,
        key="nl2sql_question"
    )

    nl2sql_button = st.button(
        "Executar NL2SQL",
        type="primary",
        key="nl2sql_button"
    )

    if nl2sql_button:

        if not nl2sql_question.strip():

            st.warning(
                "Digite uma pergunta antes de executar."
            )

        else:

            try:

                with st.spinner(
                    "Executando NL2SQL..."
                ):

                    result = ask_agent(
                        nl2sql_question
                    )

                st.success(
                    "Consulta NL2SQL executada com sucesso."
                )

                st.markdown(
                    "### 💬 Resposta"
                )

                st.write(
                    result["answer"]
                )

                st.markdown(
                    "### 🧠 SQL gerado"
                )

                st.code(
                    result["sql"],
                    language="sql"
                )

                st.markdown(
                    "### 🗄️ Resultado"
                )

                if result["rows"]:

                    result_data = [
                        dict(
                            zip(
                                result["columns"],
                                row
                            )
                        )
                        for row in result["rows"]
                    ]

                    st.dataframe(
                        result_data,
                        use_container_width=True
                    )

                else:

                    st.info(
                        "Nenhum registro foi retornado."
                    )

            except Exception as e:

                st.error(
                    "Erro durante a execução do NL2SQL."
                )

                st.exception(e)


# =========================================================
# ARQUITETURA
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🏗️ Arquitetura do projeto</div>',
    unsafe_allow_html=True
)

architecture_col1, architecture_col2 = st.columns(2)

with architecture_col1:

    st.markdown(
        """
        <div class="info-card">

        ### 📚 RAG

        **Retrieval-Augmented Generation**

        Recuperação de informações em documentos,
        seguida de geração de resposta pela LLM.

        </div>
        """,
        unsafe_allow_html=True
    )

with architecture_col2:

    st.markdown(
        """
        <div class="info-card">

        ### 🗄️ NL2SQL

        **Natural Language → SQL**

        Transformação de perguntas em consultas SQL
        para acesso aos dados estruturados do PostgreSQL.

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# OBSERVABILIDADE
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🔎 Observabilidade</div>',
    unsafe_allow_html=True
)

st.write(
    "As chamadas do Agent serão instrumentadas com OpenTelemetry."
)

obs_col1, obs_col2, obs_col3, obs_col4 = st.columns(4)

with obs_col1:

    st.metric(
        label="Traces",
        value="0"
    )

with obs_col2:

    st.metric(
        label="Tool Calls",
        value="0"
    )

with obs_col3:

    st.metric(
        label="Erros",
        value="0"
    )

with obs_col4:

    st.metric(
        label="Latência",
        value="—"
    )


# =========================================================
# RODAPÉ
# =========================================================

st.markdown(
    """
    <div class="footer">
        AI Agent Laboratory • UFRGS • OpenTelemetry
    </div>
    """,
    unsafe_allow_html=True
)
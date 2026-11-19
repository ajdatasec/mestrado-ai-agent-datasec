import streamlit as st

st.set_page_config(
    page_title="AI Agent - UFRGS",
    page_icon="🤖",
    layout="wide"
)

LOGO_URL = "https://www.inf.ufrgs.br/site/wp-content/uploads/2017/09/logo-inf-300x172.jpg"

st.markdown(
    "<div style='text-align: center;'>",
    unsafe_allow_html=True
)

st.image(LOGO_URL, width=220)

st.markdown(
    "<h2>Universidade Federal do Rio Grande do Sul</h2>",
    unsafe_allow_html=True
)

st.markdown(
    "<h1>AI Agent</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)

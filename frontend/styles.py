import streamlit as st

CSS = """
<style>
  #MainMenu, footer {visibility: hidden;}
  .block-container {padding-top: 2rem; max-width: 1100px;}
  h1 {font-weight: 700; letter-spacing: -0.02em;}
  [data-testid="stMetric"] {
    background: #F4F5FA; border: 1px solid #E5E7EB;
    border-radius: 12px; padding: 14px 18px;
  }
  [data-testid="stMetricLabel"] {color: #6B7280;}
  .login-title {text-align: center; margin-bottom: 0.2rem;}
  .login-sub {text-align: center; color: #6B7280; margin-bottom: 1.5rem;}
  .doc-name {font-weight: 600;}
  .muted {color: #6B7280; font-size: 0.85rem;}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

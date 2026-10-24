"""Small shared UI helpers."""
import plotly.graph_objects as go
import streamlit as st

COLORS = {"navy": "#16324f", "blue": "#2878b5", "teal": "#1c9a8a", "amber": "#d48b16", "red": "#c64545", "muted": "#6b7c8f"}


def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def shared_data():
    return st.session_state.get("app_data", {})


def empty_chart(message):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False, font={"color": COLORS["muted"]})
    fig.update_layout(height=300, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), xaxis={"visible": False}, yaxis={"visible": False})
    return fig

# views/components.py
import streamlit as st

def render_sidebar(venue_names):
    """サイドバーの入力フォームを描画し、ユーザーの入力値を返す"""
    st.sidebar.header("🔍 検索条件")
    selected_venue = st.sidebar.selectbox("式場を選択", venue_names)
    guests = st.sidebar.number_input("招待人数（人）", min_value=1, value=70)
    visit_type = st.sidebar.radio("区分", ["すべて", "本番", "下見"])
    submit = st.sidebar.button("費用を計算・比較")
    return selected_venue, guests, visit_type, submit
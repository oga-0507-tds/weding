import streamlit as st
from datetime import datetime
from controller.wedding_controller import WeddingController

# 画面の基本設定
st.set_page_config(
    page_title="結婚式場 費用明細 比較ツール",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(" 👑 結婚式場 費用明細 比較ツール")
st.caption("みんなのウェディングのデータをベースに、条件に合う本番・下見の平均金額を算出・比較します。")
st.write("---")

controller = WeddingController()

if "search_executed" not in st.session_state:
    st.session_state.search_executed = False
if "venue_list_loaded" not in st.session_state:
    st.session_state.venue_list_loaded = False


def close_sidebar():
    st.session_state.search_executed = True


def open_sidebar():
    st.session_state.search_executed = False


def load_venue_list():
    st.session_state.venue_list_loaded = True


def clear_venue_list():
    st.session_state.venue_list_loaded = False

# モバイル向けフォントサイズとサイドバー自動閉じ用のスタイル
def inject_mobile_styles(hide_sidebar: bool = False):
    hide_rule = "section[data-testid='stSidebar']{display:none !important;}" if hide_sidebar else ""
    st.markdown(
        f"""<style>
        html, body, .stApp, .block-container, .main {{ font-size: 13px !important; }}
        h1 {{ font-size: 1.45rem !important; }}
        h2, h3 {{ font-size: 1.15rem !important; }}
        h4, h5, h6, p, span, label, button, input, select, textarea, .stText, .stMarkdown {{ font-size: 0.95rem !important; }}
        .stButton>button, .element-container {{ font-size: 0.95rem !important; }}
        .css-1fdr9ef, .css-1nw5x17, .css-k1vhr4 {{ line-height: 1.4 !important; }}
        .css-i8vgj8, .css-14xtw13, .css-1wgvfgp {{ padding: 0.6rem 0.8rem !important; }}
        {hide_rule}
    /* selectboxのテキスト入力を無効にして、ドロップダウン選択だけにする */
    [data-testid="stSelectbox"] input[type="text"] {{
        pointer-events: none !important;
        caret-color: transparent !important;
        touch-action: none !important;
        -webkit-user-select: none !important;
        user-select: none !important;
    }}
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div > div > div:nth-child(1) {{
        pointer-events: auto !important;
    }}
        </style>""",
        unsafe_allow_html=True,
    )

inject_mobile_styles(hide_sidebar=st.session_state.search_executed)

# 画面レイアウト（スマホ対応：入力をサイドバーに移動）
with st.sidebar:
    st.header("🔍 絞り込み条件")
    st.write("## エリア選択")
    selected_areas = st.multiselect(
        "表示するエリアを選択してください",
        ["千葉", "東京"],
        default=[],
        help="両方選択すると千葉と東京の両方の式場がリストに含まれます。"
    )

    if not selected_areas:
        st.info("エリアを選択してから、式場リストを検索してください。")

    st.write("---")
    st.write("## 条件設定")
    venue_names = []
    venues = []
    if "千葉" in selected_areas:
        venues.extend(controller.get_all_venues("chiba"))
    if "東京" in selected_areas:
        venues.extend(controller.get_all_venues("tokyo"))
    venue_names = sorted({v.name for v in venues})

    selected_names = st.multiselect(
        "1. 式場を選択してください（複数選択で比較可能）", 
        venue_names,
        default=[]
    )

    st.write("2. 招待人数（範囲指定）")
    min_guests, max_guests = st.slider(
        "下限と上限を動かして指定してください",
        min_value=0,
        max_value=150,
        value=(30, 50),
        step=10
    )
    st.caption(f"現在の指定： **{min_guests}人 〜 {max_guests}人**")

    st.write("3. 時期（年月）以降")
    current_year = datetime.now().year + 1
    years = list(range(2010, current_year))
    months = list(range(1, 13))
    selected_year = st.selectbox("年", years, index=len(years)-1)
    selected_month = st.selectbox("月", months, index=0)
    since_date_str = f"{selected_year}年{selected_month:02d}月"

    cost_type = st.radio("4. データの区分", ["すべて", "本番", "下見"], index=0)

    st.write("---")
    execute_button = st.button("🚀 平均金額を計算する", type="primary", use_container_width=True, on_click=close_sidebar)

venue_by_name = {v.name: v for v in venues}

st.header("検索結果")

# サイドメニューが閉じられていても常に表示するボタン
st.button("🔧 条件を変更して再検索する", on_click=open_sidebar)

if not selected_areas:
    st.info("サイドバーからエリアを選択してください。")
elif not execute_button:
    st.info("← サイドバーのフォームで条件を設定し、「平均金額を計算する」ボタンを押してください。")
else:
    if not selected_names:
        st.warning("⚠️ 式場が選択されていません。サイドバーから1つ以上選択してください。")
    else:
        with st.spinner("データを解析しています..."):
            for name in selected_names:
                selected_venue = venue_by_name.get(name)
                if not selected_venue:
                    st.error(f"選択された式場 '{name}' の詳細情報が見つかりませんでした。")
                    continue
                try:
                    summary_dto = controller.analyze_venue_costs(
                        detail_url=selected_venue.detail_url,
                        min_guests=min_guests,
                        max_guests=max_guests,
                        since_date=since_date_str,
                        cost_type=cost_type
                    )

                    if summary_dto:
                        if summary_dto.matched_count > 0:
                            st.metric(
                                label=f"💰 {name} の平均金額 ({min_guests}〜{max_guests}人)",
                                value=f"{summary_dto.average_cost:,.1f} 円"
                            )
                            st.success(f"条件に合致する明細が {summary_dto.matched_count} 件見つかりました。")

                            with st.expander("🔗 根拠となった費用明細（口コミ）リンク", expanded=False):
                                for idx, detail in enumerate(summary_dto.details, start=1):
                                    st.markdown(
                                        f"{idx}. [{detail.wedding_date} / {detail.people_count}人 / {detail.cost_type}] "
                                        f"**{detail.amount:,}円** ➔ [明細ページを開く]({detail.detail_url})"
                                    )
                        else:
                            st.warning("⚠️ 指定された条件に合致する費用明細データが見つかりませんでした。")
                    else:
                        st.warning("⚠️ 解析結果が取得できませんでした。")
                except Exception as e:
                    st.error(f"「{name}」の解析中にエラーが発生しました: {e}")


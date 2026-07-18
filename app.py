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

# STEP 1: 式場一覧の取得
try:
    venues = controller.get_all_venues()
except Exception as e:
    st.error(f"式場一覧の取得中にエラーが発生しました: {e}")
    st.stop()

# 画面レイアウト
col_input, col_result = st.columns([1, 2])

with col_input:
    st.header("🔍 絞り込み条件")
    
    # 1. 式場選択（マルチセレクトに変更）
    venue_names = [v.name for v in venues]
    selected_names = st.multiselect(
        "1. 式場を選択してください（複数選択で比較可能）", 
        venue_names,
        default=[venue_names[0]] if venue_names else []
    )
    
    # 2. 人数範囲指定
    st.write("2. 招待人数（範囲指定）")
    min_guests, max_guests = st.slider(
        "下限と上限を動かして指定してください",
        min_value=0,
        max_value=300,
        value=(30, 50),
        step=5
    )
    st.caption(f"現在の指定： **{min_guests}人 〜 {max_guests}人**")
    
    # 3. 時期（年月）の選択
    st.write("3. 時期（年月）以降")
    current_year = datetime.now().year + 1
    years = list(range(2010, current_year))
    months = list(range(1, 13))
    
    col_y, col_m = st.columns(2)
    with col_y:
        selected_year = st.selectbox("年", years, index=len(years)-1)
    with col_m:
        selected_month = st.selectbox("月", months, index=0)
        
    since_date_str = f"{selected_year}年{selected_month:02d}月"
    
    # 4. 区分の選択
    cost_type = st.radio("4. データの区分", ["すべて", "本番", "下見"], index=0)
    
    st.write("---")
    execute_button = st.button("🚀 平均金額を計算する", type="primary", use_container_width=True)

with col_result:
    st.header("📊 解析結果")
    
    if execute_button:
        if not selected_names:
            st.warning("⚠️ 式場が選択されていません。左側のフォームから1つ以上選択してください。")
        else:
            with st.spinner("データを解析しています..."):
                # 選択された式場ごとにループ処理
                for name in selected_names:
                    # 選択された名前に合致する式場オブジェクトを特定
                    selected_venue = next(v for v in venues if v.name == name)
                    
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
    else:
        st.info("← 左側のフォームで条件を設定し、「平均金額を計算する」ボタンを押してください。")
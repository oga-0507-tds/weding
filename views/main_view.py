import streamlit as st

def render_results(result_data):
    """計算結果をメイン画面に綺麗に描画する"""
    st.title("💍 結婚式場 費用比較ダッシュボード")
    
    if result_data:
        # メトリックで大きく表示
        st.metric(label="条件に合う口コミの平均金額", value=f"{result_data['average']:,} 円")
        st.caption(f"（対象データ件数: {result_data['count']} 件）")
        
        # URLリストをリンクとして表示
        st.subheader("🔗 計算対象となった明細URL")
        for url in result_data['urls']:
            st.write(f"- [{url}]({url})")
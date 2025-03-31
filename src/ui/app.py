import streamlit as st
import requests
from common.logger import setup_logger
from common.config import API_HOST, API_PORT

# ロガーの設定
logger = setup_logger("ui")

# Streamlit UI設定
st.set_page_config(
    page_title="Knowledge Acquisition System",
    page_icon="📚",
    layout="wide",
)

# タイトルと説明
st.title("Knowledge Acquisition System")
st.write("情報収集・知識管理サブシステム")

# サイドバーナビゲーション
st.sidebar.title("メニュー")
page = st.sidebar.radio(
    "ページ選択",
    ["ダッシュボード", "データ収集", "知識検索", "設定"]
)

# APIステータス確認
def check_api_status():
    try:
        response = requests.get(f"http://{API_HOST}:{API_PORT}/health")
        if response.status_code == 200:
            return True, response.json()
        return False, {"status": "error", "code": response.status_code}
    except Exception as e:
        logger.error(f"API接続エラー: {str(e)}")
        return False, {"status": "error", "message": str(e)}

# メインコンテンツ
if page == "ダッシュボード":
    st.header("システムダッシュボード")
    
    # APIステータス表示
    st.subheader("システムステータス")
    if st.button("APIステータス確認"):
        status_ok, status_data = check_api_status()
        if status_ok:
            st.success("API接続成功：システム正常稼働中")
        else:
            st.error(f"API接続エラー：{status_data}")
    
    # システム概要
    st.subheader("システム概要")
    st.markdown("""
    このシステムは研究開発プロセスにおける知識管理を効率化するためのツールです。
    
    **主要機能：**
    - 学術論文、Webページからのデータ収集
    - テキストの前処理と構造化
    - LLMを活用した知識抽出
    - セマンティック検索機能
    - 知識グラフの構築と可視化
    """)

elif page == "データ収集":
    st.header("データ収集")
    st.write("このモジュールは現在開発中です...")
    
    # データ収集フォーム例
    st.subheader("URLからデータ収集")
    url = st.text_input("URLを入力")
    if st.button("収集開始") and url:
        st.info(f"{url} からのデータ収集をシミュレートしています...")
        # 実際の実装では、ここでAPIを呼び出してデータ収集を行う

elif page == "知識検索":
    st.header("知識検索")
    st.write("このモジュールは現在開発中です...")
    
    # 検索フォーム例
    st.subheader("セマンティック検索")
    query = st.text_input("検索クエリを入力")
    if st.button("検索") and query:
        st.info(f"「{query}」の検索をシミュレートしています...")
        # 実際の実装では、ここでAPIを呼び出して検索を行う

elif page == "設定":
    st.header("システム設定")
    st.write("このモジュールは現在開発中です...")
    
    # 設定フォーム例
    st.subheader("API設定")
    api_host = st.text_input("APIホスト", value=API_HOST)
    api_port = st.number_input("APIポート", value=API_PORT)
    if st.button("設定保存"):
        st.success("設定が保存されました（シミュレーション）")
        # 実際の実装では、ここで設定を保存する
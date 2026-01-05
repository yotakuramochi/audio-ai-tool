"""
音声配信AIアシスタント - メインエントリーポイント
"""
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# モジュールインポート
from config import log_perf, apply_custom_css
from storage import init_session_state, load_all_data
from components import (
    render_sidebar,
    render_home,
    render_script,
    render_transcriptions,
    render_script_history,
    render_settings
)


# Set page configuration
st.set_page_config(
    page_title="音声配信AIアシスタント",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)


def main():
    """メインアプリケーション"""
    log_perf("main() start")
    
    # セッション状態の初期化
    init_session_state()
    
    # LocalStorageから全データを読み込む
    load_all_data()
    log_perf("all data loaded")
    
    # カスタムCSSを適用
    apply_custom_css()
    
    # サイドバーの履歴を表示
    render_sidebar()
    
    # ヘッダー
    st.title("🎙️ 音声配信AIアシスタント")
    
    # メインナビゲーション（タブ）
    tab_home, tab_script, tab_transcripts, tab_history, tab_settings = st.tabs([
        "🏠 ホーム", "📝 台本作成", "📄 文字起こし", "📚 履歴", "⚙️ 設定"
    ])
    
    with tab_home:
        render_home()
    
    with tab_script:
        render_script()
    
    with tab_transcripts:
        render_transcriptions()
    
    with tab_history:
        render_script_history()
    
    with tab_settings:
        render_settings()
    
    log_perf("render complete")


if __name__ == "__main__":
    main()

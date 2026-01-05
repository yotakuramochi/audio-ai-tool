"""
サイドバーコンポーネント
"""
import streamlit as st
from storage import save_history_to_storage, clear_storage


def render_sidebar():
    """サイドバーに履歴を表示（ページング対応で初期DOM軽量化）"""
    if 'sidebar_show_count' not in st.session_state:
        st.session_state.sidebar_show_count = 5
    
    with st.sidebar:
        st.markdown("## 📚 生成履歴")
        
        if not st.session_state.history:
            st.markdown("*まだ履歴がありません*")
            st.markdown("音声をアップロードして概要欄を生成すると、ここに履歴が表示されます。")
        else:
            total = len(st.session_state.history)
            show_count = min(st.session_state.sidebar_show_count, total)
            st.markdown(f"*表示中: {show_count}/{total}件*")
            
            st.markdown("---")
            if st.button("🗑️ すべての履歴を削除", type="secondary", use_container_width=True):
                st.session_state.history = []
                st.session_state.viewing_history_index = None
                st.session_state.sidebar_show_count = 5
                clear_storage()
                if 'description' in st.session_state:
                    del st.session_state.description
                if 'titles' in st.session_state:
                    del st.session_state.titles
                if 'transcript' in st.session_state:
                    del st.session_state.transcript
                st.rerun()
            
            st.markdown("---")
            
            for i, item in enumerate(st.session_state.history[:show_count]):
                with st.container():
                    if st.button(
                        f"📄 {item['display_title'][:25]}...\n\n🕐 {item['datetime']}",
                        key=f"history_{i}",
                        use_container_width=True
                    ):
                        st.session_state.viewing_history_index = i
                        st.session_state.transcript = item['transcript']
                        st.session_state.description = item['description']
                        st.session_state.titles = item['titles']
                        st.rerun()
                    
                    if st.button(
                        "🗑️ この履歴を削除",
                        key=f"delete_{i}",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.session_state.history.pop(i)
                        save_history_to_storage()
                        if st.session_state.viewing_history_index == i:
                            st.session_state.viewing_history_index = None
                        st.rerun()
                    
                    st.markdown("---")
            
            if show_count < total:
                if st.button(f"📜 もっと見る（残り{total - show_count}件）", use_container_width=True):
                    st.session_state.sidebar_show_count += 5
                    st.rerun()

"""
台本履歴ページ
"""
import streamlit as st
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

from storage import save_scripts_to_storage, clear_scripts_storage


def render_script_history():
    """台本履歴ページ"""
    st.markdown("### 📚 保存した台本")
    st.markdown("作成した台本の履歴を確認できます。")
    
    if not st.session_state.saved_scripts:
        st.info("まだ保存された台本がありません。\n\n「📝 台本作成」タブで台本を作成し、「💾 履歴に保存する」ボタンで保存してください。")
        return
    
    st.markdown(f"*保存済み: {len(st.session_state.saved_scripts)}件*")
    
    if st.button("🗑️ すべての履歴を削除", type="secondary"):
        st.session_state.saved_scripts = []
        clear_scripts_storage()
        st.rerun()
    
    st.markdown("---")
    
    for i, script in enumerate(st.session_state.saved_scripts):
        with st.expander(f"📄 {script['title']} ─ {script['createdAt']}", expanded=False):
            st.markdown(script['content'])
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 コピー", key=f"copy_saved_{i}", use_container_width=True):
                    escaped_text = script['content'].replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                    streamlit_js_eval(
                        js_expressions=f"navigator.clipboard.writeText(`{escaped_text}`).then(() => true)",
                        key=f"copy_saved_script_{i}_{datetime.now().strftime('%H%M%S%f')}"
                    )
                    st.success("✅ コピーしました！")
            
            with col2:
                if st.button("🗑️ 削除", key=f"delete_saved_{i}", type="secondary", use_container_width=True):
                    st.session_state.saved_scripts.pop(i)
                    save_scripts_to_storage()
                    st.rerun()

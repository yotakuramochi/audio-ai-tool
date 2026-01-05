"""
文字起こしデータ管理画面
"""
import streamlit as st
import uuid
from datetime import datetime

from storage import save_transcriptions_to_storage, clear_transcriptions_storage


def render_transcriptions():
    """文字起こしインポート画面"""
    st.markdown("### 📄 文字起こしデータ")
    st.markdown("過去の放送の文字起こしを登録すると、あなたの口調を模倣した台本が生成されます。")
    
    st.markdown("---")
    
    # 新規登録フォーム
    with st.expander("➕ 新しい文字起こしを登録", expanded=True):
        new_title = st.text_input("📝 放送タイトル", placeholder="例: #123 副業で月5万円稼いだ話", key="new_trans_title")
        new_date = st.date_input("📅 放送日", key="new_trans_date")
        new_content = st.text_area(
            "📄 文字起こし本文",
            placeholder="音声配信の文字起こし全文を貼り付けてください...",
            height=200,
            key="new_trans_content"
        )
        new_tags = st.text_input("🏷️ タグ（カンマ区切り、任意）", placeholder="例: 副業, 収入, 体験談", key="new_trans_tags")
        
        if st.button("✅ 登録する", type="primary", use_container_width=True):
            if new_title and new_content:
                tags = [t.strip() for t in new_tags.split(",") if t.strip()] if new_tags else []
                
                new_item = {
                    'id': str(uuid.uuid4()),
                    'title': new_title,
                    'date': new_date.strftime('%Y/%m/%d'),
                    'content': new_content,
                    'tags': tags
                }
                
                st.session_state.transcriptions.insert(0, new_item)
                save_transcriptions_to_storage()
                st.success("✅ 文字起こしを登録しました！")
                st.rerun()
            else:
                st.warning("タイトルと本文を入力してください")
    
    st.markdown("---")
    
    # 登録済みデータ一覧
    st.markdown("### 📚 登録済みデータ")
    
    if not st.session_state.transcriptions:
        st.info("まだ文字起こしデータがありません。上のフォームから登録してください。")
        return
    
    st.markdown(f"*{len(st.session_state.transcriptions)}件登録済み*")
    
    if st.button("🗑️ すべて削除", type="secondary"):
        st.session_state.transcriptions = []
        clear_transcriptions_storage()
        st.rerun()
    
    st.markdown("---")
    
    for i, trans in enumerate(st.session_state.transcriptions):
        tags_str = ", ".join(trans.get('tags', [])) if trans.get('tags') else "なし"
        with st.expander(f"📄 {trans['title']} ─ {trans.get('date', '')}", expanded=False):
            st.markdown(f"**タグ:** {tags_str}")
            st.markdown("---")
            
            content = trans.get('content', '')
            if len(content) > 500:
                st.markdown(content[:500] + "...")
                if st.checkbox("全文を表示", key=f"show_full_{i}"):
                    st.markdown(content)
            else:
                st.markdown(content)
            
            st.markdown("---")
            
            if st.button("🗑️ この文字起こしを削除", key=f"delete_trans_{i}", type="secondary", use_container_width=True):
                st.session_state.transcriptions.pop(i)
                save_transcriptions_to_storage()
                st.rerun()

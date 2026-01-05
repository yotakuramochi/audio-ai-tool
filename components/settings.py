"""
設定画面
"""
import streamlit as st

from config import get_default_settings
from storage import save_settings_to_storage


def render_settings():
    """設定画面"""
    st.markdown("### ⚙️ ユーザー設定")
    st.markdown("配信スタイルやエピソードを保存して、台本作成に活用できます。")
    
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = get_default_settings()
    
    if not st.session_state.get('settings_loaded', False):
        st.info("⏳ 設定を読み込み中...")
        st.rerun()
        return
    
    settings = st.session_state.user_settings
    
    st.markdown("---")
    
    # 基本情報
    st.markdown("#### 👤 基本情報")
    
    if 'form_broadcaster' not in st.session_state:
        st.session_state.form_broadcaster = settings.get("broadcaster_name", "")
    if 'form_target' not in st.session_state:
        st.session_state.form_target = settings.get("target_audience", "")
    if 'form_style' not in st.session_state:
        st.session_state.form_style = settings.get("speaking_style", "親しみやすく")
    
    broadcaster_name = st.text_input(
        "配信者名",
        value=st.session_state.form_broadcaster,
        placeholder="例: よーちゃん",
        key="settings_broadcaster"
    )
    st.session_state.form_broadcaster = broadcaster_name
    
    target_audience = st.text_input(
        "ターゲット層",
        value=st.session_state.form_target,
        placeholder="例: 20〜30代の副業に興味がある会社員",
        key="settings_target"
    )
    st.session_state.form_target = target_audience
    
    style_options = ["親しみやすく", "丁寧に", "熱血", "毒舌"]
    current_style = st.session_state.form_style
    if current_style not in style_options:
        current_style = "親しみやすく"
    
    speaking_style = st.selectbox(
        "話し方の口調",
        options=style_options,
        index=style_options.index(current_style),
        key="settings_style"
    )
    st.session_state.form_style = speaking_style
    
    st.markdown("---")
    
    # エピソード管理
    st.markdown("#### 📖 エピソード管理")
    st.markdown("*台本作成時に、関連するエピソードが自動で選ばれます*")
    
    episodes = settings.get("episodes", [])
    
    with st.expander("➕ 新しいエピソードを追加", expanded=False):
        new_title = st.text_input("エピソードのタイトル", placeholder="例: 副業で初めて1万円稼いだ話", key="new_ep_title")
        new_detail = st.text_area("詳細", placeholder="どんな経験だったか、学びなどを記載", key="new_ep_detail", height=100)
        
        if st.button("✅ エピソードを追加", key="add_episode"):
            if new_title and new_detail:
                episodes.append({"title": new_title, "detail": new_detail})
                st.session_state.user_settings["episodes"] = episodes
                save_settings_to_storage()
                st.success("エピソードを追加しました！")
                st.rerun()
            else:
                st.warning("タイトルと詳細を入力してください")
    
    if episodes:
        st.markdown(f"*登録済み: {len(episodes)}件*")
        for i, ep in enumerate(episodes):
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{ep['title']}**")
                    st.caption(ep['detail'][:100] + "..." if len(ep['detail']) > 100 else ep['detail'])
                with col2:
                    if st.button("🗑️", key=f"del_ep_{i}"):
                        episodes.pop(i)
                        st.session_state.user_settings["episodes"] = episodes
                        save_settings_to_storage()
                        st.rerun()
                st.markdown("---")
    else:
        st.info("まだエピソードが登録されていません")
    
    # 保存ボタン
    st.markdown("---")
    if st.button("💾 設定を保存", type="primary", use_container_width=True):
        st.session_state.user_settings = {
            "broadcaster_name": broadcaster_name,
            "target_audience": target_audience,
            "speaking_style": speaking_style,
            "episodes": episodes
        }
        st.session_state.form_broadcaster = broadcaster_name
        st.session_state.form_target = target_audience
        st.session_state.form_style = speaking_style
        
        save_settings_to_storage()
        st.success("✅ 設定を保存しました！")
        st.balloons()

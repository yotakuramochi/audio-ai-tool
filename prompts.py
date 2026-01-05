"""
AIプロンプトテンプレート
"""
import re


def get_transcription_prompt():
    """文字起こし用プロンプト"""
    return """
この音声ファイルを文字起こししてください。

【指示】
- 話された内容を一言一句漏らさず書き起こす
- 「えー」「あー」「うーん」などのフィラー（つなぎ言葉）は除去する
- 言い直しや重複は整理して読みやすくする
- 段落分けして見やすく整形する
- 要約はせず、必ず全文を書き起こすこと

【出力形式】
文字起こしのテキストのみを出力してください。余計な説明は不要です。
"""


def get_combined_prompt(transcript):
    """概要欄とタイトルを同時生成するプロンプト（API節約）"""
    return f"""
以下の文字起こしを元に、「概要欄」と「タイトル案3つ」を同時に作成してください。

【文字起こし】
{transcript}

===== 出力形式（この形式を厳守）=====

---DESCRIPTION_START---
▼このチャンネルでは
理学療法士、Webライター、副業、インタビュー企画など、実体験をもとに発信しています。
"今、挑戦している人"の背中を押せるような内容を目指しています。

▪️X（旧Twitter）
https://x.com/kurayota0714

▪️おもろい図鑑
https://omoroi-zukan.jp/

【AI要約】
（ここに整形した文字起こしを出力。話し言葉を残しつつ読みやすく整形。要約ではなく全文を整形。）
---DESCRIPTION_END---

---TITLES_START---
1. タイトル案1（30文字以内、キャッチーに）
2. タイトル案2（30文字以内、キャッチーに）
3. タイトル案3（30文字以内、キャッチーに）
---TITLES_END---
"""


def get_script_prompt(memo, settings, selected_episodes):
    """台本生成用プロンプト"""
    style_guide = {
        "親しみやすく": "フレンドリーで親近感のある話し方。「〜だよね」「〜かな」など。",
        "丁寧に": "敬語を使い、落ち着いた丁寧な話し方。「〜です」「〜ますね」など。",
        "熱血": "情熱的でエネルギッシュな話し方。「絶対に〜！」「〜しようぜ！」など。",
        "毒舌": "ズバッと本音を言う話し方。皮肉やユーモアを交えて。"
    }
    
    style = settings.get("speaking_style", "親しみやすく")
    style_description = style_guide.get(style, style_guide["親しみやすく"])
    
    episodes_text = ""
    if selected_episodes:
        episodes_text = "\n\n【関連エピソード（台本に組み込むこと）】\n"
        for ep in selected_episodes:
            episodes_text += f"・{ep['title']}: {ep['detail']}\n"
    
    broadcaster = settings.get("broadcaster_name", "")
    target = settings.get("target_audience", "")
    
    return f"""
以下のメモを元に、音声配信（5〜7分、約1,500〜2,000文字）用の台本を作成してください。

【配信者情報】
- 名前: {broadcaster if broadcaster else "未設定"}
- ターゲット: {target if target else "一般リスナー"}
- 口調: {style}（{style_description}）

【メモ】
{memo}
{episodes_text}

【台本のルール】
1. Markdownの見出し（##）を必ず使う（オープニング、メインパート、クロージングなど）
2. 箇条書き形式で話すポイントを記載（完全な文章でなくてよい）
3. 1,500〜2,000文字で作成する
4. 関連エピソードがある場合は自然に組み込む
5. 指定された口調で統一する

【出力形式】
## オープニング
- 挨拶
- 今日のテーマ紹介

## メインパート
（内容に応じてセクション分け）

## クロージング
- まとめ
- 次回予告や告知
"""


def search_relevant_transcriptions(memo_text, transcriptions, max_results=2):
    """メモからキーワードを抽出し、関連する文字起こしを検索（簡易RAG）"""
    if not transcriptions or not memo_text:
        return []
    
    words = re.split(r'[、。！？\s\n・「」『』（）\(\)]+', memo_text)
    keywords = [w.strip() for w in words if len(w.strip()) >= 2]
    
    if not keywords:
        return transcriptions[:max_results]
    
    scored_transcriptions = []
    for trans in transcriptions:
        score = 0
        content = trans.get('content', '') + ' ' + trans.get('title', '')
        tags = trans.get('tags', [])
        
        for keyword in keywords:
            if keyword in content:
                score += content.count(keyword)
            for tag in tags:
                if keyword in tag or tag in keyword:
                    score += 3
        
        if score > 0:
            scored_transcriptions.append((trans, score))
    
    scored_transcriptions.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in scored_transcriptions[:max_results]]


def get_script_prompt_with_transcriptions(memo, settings, transcriptions):
    """文字起こしデータを参考にした台本生成用プロンプト（RAG版）"""
    style_guide = {
        "親しみやすく": "フレンドリーで親近感のある話し方。「〜だよね」「〜かな」など。",
        "丁寧に": "敬語を使い、落ち着いた丁寧な話し方。「〜です」「〜ますね」など。",
        "熱血": "情熱的でエネルギッシュな話し方。「絶対に〜！」「〜しようぜ！」など。",
        "毒舌": "ズバッと本音を言う話し方。皮肉やユーモアを交えて。"
    }
    
    style = settings.get("speaking_style", "親しみやすく")
    style_description = style_guide.get(style, style_guide["親しみやすく"])
    
    broadcaster = settings.get("broadcaster_name", "")
    target = settings.get("target_audience", "")
    
    reference_text = ""
    if transcriptions:
        reference_text = "\n\n【参考資料（過去の語り口調サンプル）】\n"
        reference_text += "以下は、このユーザーが過去に実際に話した文字起こしです。\n"
        reference_text += "これらと同様の『口調』『リズム』『言葉選び』を模倣して台本を作成してください。\n\n"
        for i, trans in enumerate(transcriptions, 1):
            content = trans.get('content', '')[:1000]
            if len(trans.get('content', '')) > 1000:
                content += "..."
            reference_text += f"--- サンプル{i}: {trans.get('title', '無題')} ---\n{content}\n\n"
    
    return f"""
以下のメモを元に、音声配信（5〜7分、約1,500〜2,000文字）用の台本を作成してください。

【配信者情報】
- 名前: {broadcaster if broadcaster else "未設定"}
- ターゲット: {target if target else "一般リスナー"}
- 口調: {style}（{style_description}）

【メモ】
{memo}
{reference_text}

【台本のルール】
1. Markdownの見出し（##）を必ず使う（オープニング、メインパート、クロージングなど）
2. 箇条書き形式で話すポイントを記載（完全な文章でなくてよい）
3. 1,500〜2,000文字で作成する
4. 参考資料がある場合は、その口調やリズムを参考にする
5. 指定された口調で統一する

【出力形式】
## オープニング
- 挨拶
- 今日のテーマ紹介

## メインパート
（内容に応じてセクション分け）

## クロージング
- まとめ
- 次回予告や告知
"""

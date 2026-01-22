import streamlit as st
import pandas as pd
from datetime import datetime
import time
import requests
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="Ramadan Series Monitor 2026",
    page_icon="📡",
    layout="wide"
)

def inject_custom_css(dark_mode):
    bg_color = "#0e1117" if dark_mode else "#ffffff"
    text_color = "#fafafa" if dark_mode else "#000000"
    card_bg = "#262730" if dark_mode else "#f0f2f6"
    
    st.markdown(f"""
    <style>
        .stApp {{background-color: {bg_color}; color: {text_color};}}
        .result-card {{
            background-color: {card_bg};
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #4b4b4b;
        }}
        .stats-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True)

if 'results' not in st.session_state:
    st.session_state.results = []
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'translations' not in st.session_state:
    st.session_state.translations = {}

with st.sidebar:
    st.header("⚙️ إعدادات المنصة")
    
    dark_mode_btn = st.toggle('🌙 الوضع الليلي', value=st.session_state.dark_mode)
    if dark_mode_btn != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode_btn
        st.rerun()

    st.divider()
    
    st.subheader("🔑 مفاتيح API")
    youtube_key = st.text_input("YouTube API Key", type="AIzaSyDnhSmVac0ic9yt3OregsSgZYZwXUUvOTU")
    news_key = st.text_input("NewsAPI Key", type="1aa5d0dd3775438a8e573ee6ed184ee0")
    
    st.divider()
    uploaded_file = st.file_uploader("ارفع ملف الإكسل", type=['xlsx'])
    
    platforms = st.multiselect(
        "المنصات:",
        ["YouTube", "News"],
        default=["YouTube"]
    )
    
    st.divider()
    if st.button("🗑️ مسح النتائج"):
        st.session_state.results = []
        st.session_state.translations = {}
        st.rerun()

inject_custom_css(st.session_state.dark_mode)

def translate_text(text, index):
    if index in st.session_state.translations:
        return st.session_state.translations[index]
    try:
        translated = GoogleTranslator(source='auto', target='ar').translate(text[:500])
        st.session_state.translations[index] = translated
        return translated
    except:
        return "خطأ في الترجمة"

def search_youtube(keyword, language, api_key):
    results = []
    if not api_key:
        return results
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': keyword,
            'type': 'video',
            'maxResults': 5,
            'key': api_key
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'items' in data:
            for item in data['items']:
                video_id = item['id'].get('videoId', '')
                title = item['snippet'].get('title', '')
                
                results.append({
                    "Platform": "YouTube",
                    "Keyword": keyword,
                    "Language": language,
                    "Content": title,
                    "Link": f"https://www.youtube.com/watch?v={video_id}",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    except:
        pass
    return results

st.title("📡 رادار ترجمات مسلسلات رمضان 2026")
st.markdown("---")

if not youtube_key and not news_key:
    st.warning("⚠️ أدخل مفتاح API في الشريط الجانبي")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    with st.expander("الكلمات المفتاحية"):
        st.dataframe(df.head())
    
    languages = [col for col in df.columns if 'Unnamed' not in col]
    selected_langs = st.multiselect("اللغات:", languages, default=languages[:2] if len(languages)>=2 else languages)
    
    if st.button("🚀 ابدأ الرصد", type="primary"):
        if youtube_key or news_key:
            progress = st.progress(0)
            status = st.empty()
            
            total = len(df) * len(selected_langs)
            current = 0
            
            for _, row in df.iterrows():
                for lang in selected_langs:
                    keywords_raw = str(row.get(lang, ''))
                    if keywords_raw and keywords_raw != 'nan':
                        keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]
                        
                        for keyword in keywords[:2]:
                            status.text(f"🔍 {keyword} ({lang})")
                            
                            if "YouTube" in platforms and youtube_key:
                                new_res = search_youtube(keyword, lang, youtube_key)
                                st.session_state.results.extend(new_res)
                            
                            current += 1
                            progress.progress(min(current/total, 1.0))
                            time.sleep(1)
            
            status.success(f"✅ تم! {len(st.session_state.results)} نتيجة")
            time.sleep(1)
            st.rerun()

if st.session_state.results:
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(st.session_state.results)}</h2><p>النتائج</p></div>', unsafe_allow_html=True)
    
    st.subheader("📊 النتائج")
    res_df = pd.DataFrame(st.session_state.results)
    
    for i, row in res_df.iterrows():
        st.markdown(f"""
        <div class="result-card">
            <h4>📺 {row['Platform']} | 🌐 {row['Language']}</h4>
            <p><strong>{row['Keyword']}</strong></p>
            <p>{row['Content'][:200]}</p>
            <a href="{row['Link']}" target="_blank">🔗 المصدر</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 ترجم", key=f"t_{i}"):
            with st.spinner("..."):
                trans = translate_text(row['Content'], i)
                st.info(trans)
else:
    st.info("ارفع ملف Excel واضغط ابدأ الرصد")

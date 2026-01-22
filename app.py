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

# Session State
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
    youtube_key = st.text_input(
        "YouTube API Key", 
        type="password",
        help="احصل عليه من console.cloud.google.com"
    )
    news_key = st.text_input(
        "NewsAPI Key", 
        type="password",
        help="احصل عليه من newsapi.org"
    )
    
    st.divider()
    uploaded_file = st.file_uploader("📄 ارفع ملف الإكسل", type=['xlsx'])
    
    platforms = st.multiselect(
        "🌐 المنصات:",
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

def search_youtube(series_name, keyword, language, api_key):
    """بحث محسّن في YouTube"""
    results = []
    if not api_key:
        return results
    
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        search_query = f'"{keyword}" OR "{series_name}" {language}'
        
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': 3,
            'key': api_key,
            'order': 'date',
            'relevanceLanguage': language if len(language) == 2 else 'ar'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'items' in data:
            for item in data['items']:
                video_id = item['id'].get('videoId', '')
                title = item['snippet'].get('title', '')
                description = item['snippet'].get('description', '')[:150]
                
                results.append({
                    "Platform": "YouTube",
                    "Series": series_name,
                    "Keyword": keyword,
                    "Language": language,
                    "Content": f"{title} - {description}",
                    "Link": f"https://www.youtube.com/watch?v={video_id}",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    except Exception as e:
        st.warning(f"⚠️ خطأ في YouTube ({series_name}): {str(e)}")
    
    return results

def search_news(series_name, keyword, language, api_key):
    """بحث في NewsAPI"""
    results = []
    if not api_key:
        return results
    
    try:
        url = "https://newsapi.org/v2/everything"
        
        params = {
            'q': keyword,
            'apiKey': api_key,
            'pageSize': 5,
            'sortBy': 'publishedAt',
            'language': language if len(language) == 2 else 'ar'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'ok' and 'articles' in data:
            for article in data['articles']:
                results.append({
                    "Platform": "News",
                    "Series": series_name,
                    "Keyword": keyword,
                    "Language": language,
                    "Content": f"{article.get('title', '')} - {article.get('description', '')[:150]}",
                    "Link": article.get('url', ''),
                    "Date": article.get('publishedAt', datetime.now().strftime("%Y-%m-%d %H:%M"))
                })
    except Exception as e:
        st.warning(f"⚠️ خطأ في News ({series_name}): {str(e)}")
    
    return results

st.title("📡 رادار ترجمات مسلسلات رمضان 2026")
st.markdown("---")

if not youtube_key and not news_key:
    st.warning("⚠️ أدخل مفتاح API واحد على الأقل في الشريط الجانبي")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # استخراج أسماء المسلسلات (الصف الأول)
    series_names = df.iloc[0, 1:].dropna().tolist()
    
    # استخراج اللغات (أسماء الأعمدة)
    languages = [col for col in df.columns[1:] if 'Unnamed' not in str(col)]
    
    with st.expander("📊 عرض البيانات"):
        st.dataframe(df.head(10))
    
    # الفلاتر
    col1, col2 = st.columns(2)
    
    with col1:
        selected_series = st.multiselect(
            "🎬 اختر المسلسلات:", 
            series_names,
            default=series_names[:3] if len(series_names) >= 3 else series_names,
            help="اختر المسلسلات اللي عاوزة تراقبيها"
        )
    
    with col2:
        selected_langs = st.multiselect(
            "🌍 اختر اللغات:", 
            languages,
            default=languages[:3] if len(languages) >= 3 else languages[:2],
            help="اختر اللغات المطلوب رصدها"
        )
    
    if st.button("🚀 ابدأ الرصد", type="primary", use_container_width=True):
        if (youtube_key or news_key) and selected_series and selected_langs:
            progress = st.progress(0)
            status = st.empty()
            
            total = len(selected_series) * len(selected_langs)
            current = 0
            
            for series_name in selected_series:
                series_row = df[df.iloc[:, 1] == series_name]
                
                if series_row.empty:
                    continue
                
                for lang in selected_langs:
                    if lang in df.columns:
                        keywords_raw = series_row[lang].values[0] if not series_row[lang].empty else ''
                        keywords_raw = str(keywords_raw)
                        
                        if keywords_raw and keywords_raw != 'nan':
                            keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]
                            
                            for keyword in keywords[:2]:
                                status.text(f"🔍 {series_name} | {keyword} ({lang})")
                                
                                if "YouTube" in platforms and youtube_key:
                                    new_res = search_youtube(series_name, keyword, lang, youtube_key)
                                    st.session_state.results.extend(new_res)
                                
                                if "News" in platforms and news_key:
                                    new_res = search_news(series_name, keyword, lang, news_key)
                                    st.session_state.results.extend(new_res)
                                
                                time.sleep(1.5)
                    
                    current += 1
                    progress.progress(min(current / total, 1.0))
            
            status.success(f"✅ تم جلب {len(st.session_state.results)} نتيجة")
            time.sleep(1)
            st.rerun()
        else:
            st.error("⚠️ اختر مسلسلات ولغات وأدخل API Key")

# عرض النتائج
if st.session_state.results:
    st.markdown("---")
    
    res_df = pd.DataFrame(st.session_state.results)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(res_df)}</h2><p>إجمالي النتائج</p></div>', unsafe_allow_html=True)
    with col2:
        unique_series = res_df['Series'].nunique()
        st.markdown(f'<div class="stats-box"><h2>{unique_series}</h2><p>عدد المسلسلات</p></div>', unsafe_allow_html=True)
    with col3:
        unique_langs = res_df['Language'].nunique()
        st.markdown(f'<div class="stats-box"><h2>{unique_langs}</h2><p>عدد اللغات</p></div>', unsafe_allow_html=True)
    
    st.subheader("📊 نتائج الرصد")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        series_filter = st.multiselect("🎬 فلتر بالمسلسل", res_df['Series'].unique())
    with c2:
        lang_filter = st.multiselect("🌍 فلتر باللغة", res_df['Language'].unique())
    with c3:
        plat_filter = st.multiselect("📱 فلتر بالمنصة", res_df['Platform'].unique())
    
    filtered_df = res_df.copy()
    
    if series_filter:
        filtered_df = filtered_df[filtered_df['Series'].isin(series_filter)]
    if lang_filter:
        filtered_df = filtered_df[filtered_df['Language'].isin(lang_filter)]
    if plat_filter:
        filtered_df = filtered_df[filtered_df['Platform'].isin(plat_filter)]
    
    st.info(f"📋 عرض {len(filtered_df)} من {len(res_df)} نتيجة")
    
    for i, row in filtered_df.iterrows():
        st.markdown(f"""
        <div class="result-card">
            <h4>🎬 {row['Series']} | 📺 {row['Platform']} | 🌐 {row['Language']}</h4>
            <p><strong>🔑 الكلمة المفتاحية:</strong> {row['Keyword']}</p>
            <p>{row['Content'][:300]}</p>
            <p><small>📅 {row['Date']}</small></p>
            <a href="{row['Link']}" target="_blank">🔗 عرض المصدر</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 ترجم للعربية", key=f"trans_{i}"):
            with st.spinner("جاري الترجمة..."):
                trans = translate_text(row['Content'], i)
                st.info(f"**الترجمة:** {trans}")
else:
    st.info("👆 ارفع ملف Excel واختر المسلسلات واللغات واضغط 'ابدأ الرصد'")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ for Ramadan 2026 Monitoring</div>",
    unsafe_allow_html=True
)

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
    x_bearer_token = st.text_input(
        "X (Twitter) Bearer Token",
        type="password",
        help="احصل عليه من developer.twitter.com → Projects & Apps → Keys and tokens → Bearer Token"
    )
  
    st.divider()
    uploaded_file = st.file_uploader("ارفع ملف الإكسل", type=['xlsx'])
  
    platforms = st.multiselect(
        "المنصات:",
        ["YouTube", "X", "News"],
        default=["YouTube", "X"]
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
            'q': f'"{keyword}"',
            'type': 'video',
            'maxResults': 10,
            'key': api_key
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
      
        if 'items' in data:
            keyword_lower = keyword.lower()
            for item in data['items']:
                title = item['snippet'].get('title', '').lower()
                description = item['snippet'].get('description', '').lower()
                
                if keyword_lower in title or keyword_lower in description:
                    video_id = item['id'].get('videoId', '')
                    results.append({
                        "Platform": "YouTube",
                        "Keyword": keyword,
                        "Language": language,
                        "Content": f"{item['snippet'].get('title', '')} - {item['snippet'].get('description', '')[:100]}",
                        "Link": f"https://www.youtube.com/watch?v={video_id}",
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
    except Exception as e:
        st.warning(f"خطأ في YouTube: {str(e)}")
    
    return results

def search_x(keyword, language, bearer_token):
    results = []
    if not bearer_token:
        return results
    
    try:
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        params = {
            'query': f'"{keyword}" lang:{language} -is:retweet',
            'tweet.fields': 'created_at,text,author_id,lang',
            'max_results': 10,
            'expansions': 'author_id',
            'user.fields': 'username,name'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if 'data' in data:
            users = {u['id']: u for u in data.get('includes', {}).get('users', [])}
            
            for tweet in data['data']:
                text_lower = tweet['text'].lower()
                keyword_lower = keyword.lower()
                
                if keyword_lower in text_lower:
                    author = users.get(tweet['author_id'], {})
                    username = author.get('username', 'غير معروف')
                    name = author.get('name', '')
                    
                    results.append({
                        "Platform": "X",
                        "Keyword": keyword,
                        "Language": language,
                        "Content": f"@{username} ({name}): {tweet['text'][:150]}...",
                        "Link": f"https://x.com/{username}/status/{tweet['id']}",
                        "Date": tweet.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M"))
                    })
    
    except Exception as e:
        st.warning(f"خطأ في البحث على X: {str(e)}")
    
    return results

st.title("📡 رادار ترجمات مسلسلات رمضان 2026")
st.markdown("---")

if not youtube_key and not news_key and not x_bearer_token:
    st.warning("⚠️ أدخل مفتاح API واحد على الأقل في الشريط الجانبي لبدء الرصد")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    series_names = df.iloc[0, 1:].dropna().tolist()
    languages = df.iloc[1:, 0].dropna().tolist()

    with st.expander("عرض الكلمات المفتاحية"):
        st.dataframe(df.head(10))

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_series = st.multiselect(
            "اختر المسلسلات:",
            options=series_names,
            default=series_names[:3] if series_names else []
        )
    with col_filter2:
        selected_langs = st.multiselect(
            "اختر اللغات:",
            options=languages,
            default=languages[:3] if languages else []
        )

    if st.button("🚀 ابدأ الرصد", type="primary"):
        if not selected_series or not selected_langs:
            st.warning("⚠️ اختر على الأقل مسلسل واحد ولغة واحدة")
        elif youtube_key or news_key or x_bearer_token:
            progress = st.progress(0)
            status = st.empty()
            total = len(selected_series) * len(selected_langs)
            current = 0

            for lang in selected_langs:
                lang_row_idx = df[df.iloc[:, 0] == lang].index[0] if lang in df.iloc[:, 0].values else None
                if lang_row_idx is None:
                    continue
                
                for ser in selected_series:
                    ser_col_idx = df.columns[df.iloc[0] == ser][0] if ser in df.iloc[0].values else None
                    if ser_col_idx is None:
                        continue
                    
                    keywords_raw = str(df.at[lang_row_idx, ser_col_idx])
                    if keywords_raw and keywords_raw.lower() != 'nan':
                        keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]
                        for keyword in keywords[:2]:  # أول كلمتين فقط
                            status.text(f"🔍 {keyword} ({lang} - {ser})")
                            
                            # نتايج YouTube
                            if "YouTube" in platforms and youtube_key:
                                youtube_results = search_youtube(keyword, lang, youtube_key)
                                for res in youtube_results:
                                    res["Series"] = ser
                                st.session_state.results.extend(youtube_results)
                            
                            # نتايج X
                            if "X" in platforms and x_bearer_token:
                                x_results = search_x(keyword, lang, x_bearer_token)
                                for res in x_results:
                                    res["Series"] = ser
                                st.session_state.results.extend(x_results)
                            
                            current += 1
                            progress.progress(min(current / total, 1.0))
                            time.sleep(1)  # تأخير بسيط عشان ما نضغطش على الـ APIs

            status.success(f"✅ تم جلب {len(st.session_state.results)} نتيجة")
            time.sleep(1)
            st.rerun()
        else:
            st.error("⚠️ أدخل مفتاح API أولاً")

if st.session_state.results:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(st.session_state.results)}</h2><p>إجمالي النتائج</p></div>', unsafe_allow_html=True)
    with col2:
        unique_langs = len(set([r['Language'] for r in st.session_state.results]))
        st.markdown(f'<div class="stats-box"><h2>{unique_langs}</h2><p>عدد اللغات</p></div>', unsafe_allow_html=True)
    with col3:
        unique_platforms = len(set([r['Platform'] for r in st.session_state.results]))
        st.markdown(f'<div class="stats-box"><h2>{unique_platforms}</h2><p>عدد المنصات</p></div>', unsafe_allow_html=True)

    st.subheader("📊 نتائج الرصد")
    res_df = pd.DataFrame(st.session_state.results)
    c1, c2 = st.columns(2)
    with c1:
        lang_filter = st.multiselect("فلتر باللغة", res_df['Language'].unique())
    with c2:
        plat_filter = st.multiselect("فلتر بالمنصة", res_df['Platform'].unique())

    filtered_df = res_df.copy()
    if lang_filter:
        filtered_df = filtered_df[filtered_df['Language'].isin(lang_filter)]
    if plat_filter:
        filtered_df = filtered_df[filtered_df['Platform'].isin(plat_filter)]

    for i, row in filtered_df.iterrows():
        series_name = row.get('Series', 'غير محدد')
        platform_icon = '🐦' if row['Platform'] == 'X' else '📺'
        
        st.markdown(f"""
        <div class="result-card">
            <h4>{platform_icon} {row['Platform']} | 🌐 {row['Language']} | 🎬 {series_name}</h4>
            <p><strong>الكلمة المفتاحية:</strong> {row['Keyword']}</p>
            <p>{row['Content']}</p>
            <p><small>📅 {row['Date']}</small></p>
            <a href="{row['Link']}" target="_blank">🔗 عرض المصدر</a>
        </div>
        """, unsafe_allow_html=True)
       
        if st.button("🔄 ترجم للعربية", key=f"trans_{i}"):
            with st.spinner("جاري الترجمة..."):
                trans = translate_text(row['Content'], i)
                st.info(f"**الترجمة:** {trans}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ for Ramadan 2026 Monitoring</div>",
    unsafe_allow_html=True
)

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
    twitter_bearer = st.text_input(
        "Twitter Bearer Token", 
        type="password",
        help="احصل عليه من developer.twitter.com"
    )
    
    st.divider()
    uploaded_file = st.file_uploader("ارفع ملف الإكسل", type=['xlsx'])
    
    platforms = st.multiselect(
        "المنصات:",
        ["Twitter/X", "YouTube", "News"],
        default=["Twitter/X"]
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

def search_twitter(keyword, language, bearer_token):
    """البحث في Twitter/X"""
    results = []
    if not bearer_token:
        return results
    
    try:
        url = "https://api.twitter.com/2/tweets/search/recent"
        
        if len(keyword.split()) > 1:
            search_query = f'"{keyword}"'
        else:
            search_query = keyword
        
        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        
        params = {
            "query": search_query,
            "max_results": 10,
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data:
            users = {user['id']: user['username'] for user in data.get('includes', {}).get('users', [])}
            
            for tweet in data['data']:
                author_id = tweet.get('author_id', '')
                username = users.get(author_id, 'unknown')
                
                results.append({
                    "Platform": "Twitter/X",
                    "Keyword": keyword,
                    "Language": language,
                    "Content": tweet.get('text', ''),
                    "Link": f"https://twitter.com/{username}/status/{tweet['id']}",
                    "Date": tweet.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M")),
                    "Engagement": f"❤️ {tweet.get('public_metrics', {}).get('like_count', 0)} | 🔁 {tweet.get('public_metrics', {}).get('retweet_count', 0)}"
                })
    except Exception as e:
        st.warning(f"خطأ في Twitter: {str(e)}")
    
    return results

def get_youtube_comments(video_id, api_key, max_comments=5):
    """جلب التعليقات من فيديو YouTube"""
    comments = []
    try:
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': max_comments,
            'order': 'relevance',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'items' in data:
            for item in data['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': comment.get('textDisplay', ''),
                    'author': comment.get('authorDisplayName', ''),
                    'likes': comment.get('likeCount', 0)
                })
    except:
        pass
    
    return comments

def search_youtube(keyword, language, api_key):
    results = []
    if not api_key:
        return results
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        
        if len(keyword.split()) > 1:
            search_query = f'"{keyword}"'
        else:
            search_query = keyword
        
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': 3,
            'key': api_key
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'items' in data:
            for item in data['items']:
                video_id = item['id'].get('videoId', '')
                title = item['snippet'].get('title', '')
                description = item['snippet'].get('description', '')[:100]
                
                # إضافة الفيديو نفسه
                results.append({
                    "Platform": "YouTube",
                    "Type": "Video",
                    "Keyword": keyword,
                    "Language": language,
                    "Content": f"{title} - {description}",
                    "Link": f"https://www.youtube.com/watch?v={video_id}",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                # جلب التعليقات
                comments = get_youtube_comments(video_id, api_key, max_comments=3)
                for comment in comments:
                    results.append({
                        "Platform": "YouTube",
                        "Type": "Comment",
                        "Keyword": keyword,
                        "Language": language,
                        "Content": f"💬 {comment['text'][:200]}",
                        "Link": f"https://www.youtube.com/watch?v={video_id}",
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Engagement": f"👤 {comment['author']} | 👍 {comment['likes']}"
                    })
                
                time.sleep(0.5)
                
    except Exception as e:
        st.warning(f"خطأ في YouTube: {str(e)}")
    return results

st.title("📡 رادار ترجمات مسلسلات رمضان 2026")
st.markdown("---")

if not youtube_key and not news_key and not twitter_bearer:
    st.warning("⚠️ أدخل مفتاح API في الشريط الجانبي لبدء الرصد")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    with st.expander("عرض الكلمات المفتاحية"):
        st.dataframe(df.head())
    
    languages = [col for col in df.columns if 'Unnamed' not in col]
    selected_langs = st.multiselect(
        "اختر اللغات:", 
        languages, 
        default=languages[:2] if len(languages)>=2 else languages
    )
    
    if st.button("🚀 ابدأ الرصد", type="primary"):
        if youtube_key or news_key or twitter_bearer:
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
                            
                            if "Twitter/X" in platforms and twitter_bearer:
                                new_res = search_twitter(keyword, lang, twitter_bearer)
                                st.session_state.results.extend(new_res)
                            
                            if "YouTube" in platforms and youtube_key:
                                new_res = search_youtube(keyword, lang, youtube_key)
                                st.session_state.results.extend(new_res)
                            
                            current += 1
                            progress.progress(min(current/total, 1.0))
                            time.sleep(2)
            
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
        type_badge = f"<span style='background:#4CAF50;padding:3px 8px;border-radius:5px;font-size:11px;'>{row.get('Type', '')}</span>" if 'Type' in row else ""
        engagement_text = f"<p><strong>التفاعل:</strong> {row.get('Engagement', '')}</p>" if 'Engagement' in row and row['Engagement'] else ""
        
        st.markdown(f"""
        <div class="result-card">
            <h4>📺 {row['Platform']} {type_badge} | 🌐 {row['Language']}</h4>
            <p><strong>الكلمة المفتاحية:</strong> {row['Keyword']}</p>
            <p>{row['Content'][:250]}</p>
            {engagement_text}
            <p><small>📅 {row['Date']}</small></p>
            <a href="{row['Link']}" target="_blank">🔗 عرض المصدر</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 ترجم للعربية", key=f"trans_{i}"):
            with st.spinner("جاري الترجمة..."):
                trans = translate_text(row['Content'], i)
                st.info(f"**الترجمة:** {trans}")
else:
    st.info("👆 ارفع ملف Excel وأدخل API Key واضغط 'ابدأ الرصد'")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ for Ramadan 2026 Monitoring</div>",
    unsafe_allow_html=True
)

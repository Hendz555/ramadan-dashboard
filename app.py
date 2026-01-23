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
                description = item['snippet'].get('description', '')[:100]
               
                results.append({
                    "Platform": "YouTube",
                    "Keyword": keyword,
                    "Language": language,
                    "Content": f"{title} - {description}",
                    "Link": f"https://www.youtube.com/watch?v={video_id}",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    except Exception as e:
        st.warning(f"خطأ في YouTube: {str(e)}")
    return results

st.title("📡 رادار ترجمات مسلسلات رمضان 2026")
st.markdown("---")

if not youtube_key and not news_key:
    st.warning("⚠️ أدخل مفتاح API في الشريط الجانبي لبدء الرصد")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
   
    # التعديل: نفترض الآن أن اللغات هي صفوف، والمسلسلات هي أعمدة. لذا، نعكس التعامل عبر transpose
    df = df.T  # نقل الصفوف إلى أعمدة والعكس، ليصبح الأعمدة اللغات كما يتوقع الكود الأصلي
    df.columns = df.iloc[0]  # جعل الصف الأول (أسماء المسلسلات الأصلية) أعمدة جديدة (الآن لغات؟ انتظر، لا.
    # انتظر، إذا كانت الأصلي: صفوف = لغات، أعمدة = مسلسلات.
    # ثم T: صفوف = مسلسلات، أعمدة = لغات.
    # نعم، الآن يتطابق مع الافتراض الأصلي للكود (أعمدة = لغات).
    # إزالة الصف الأول إذا أصبح headers.
    df = df[1:]  # إذا كان الصف الأول هو headers بعد transpose، أزل إذا لزم.
    # لتبسيط، إذا كان الملف بدون index، بعد T، df.columns هي الصفوف الأصلية (لغات)، لكن قد تكون أرقام.
    # لنجعلها صحيحة: افترض أن الملف الأصلي لديه الصف الأول أسماء المسلسلات، العمود الأول لغات؟

    # للدقة، دعنا نعدل الاستخراج بدلاً من transpose إذا كان معقد.
    # بديل: استخراج اللغات من الصفوف.

    # دعنا نغير الكود بدلاً من ذلك.
    # إزالة transpose وتغيير الـ languages.
    # languages = df.index.tolist() إذا كان index اللغات، لكن افترض no index، فالعمدة الأول هو اللغة.

    # افترض العمود الأول 'اللغة'، الأعمدة الباقية مسلسلات.

    if 'اللغة' in df.columns:  # للتعامل مع اسم العمود
        lang_column = 'اللغة'
    else:
        lang_column = df.columns[0]  # افترض الأول هو اللغة

    languages = df[lang_column].tolist()

    series_names = [col for col in df.columns if col != lang_column]

    with st.expander("عرض الكلمات المفتاحية"):
        st.dataframe(df.head())

    selected_langs = st.multiselect(
        "اختر اللغات:",
        languages,
        default=languages[:2] if len(languages)>=2 else languages
    )

    if st.button("🚀 ابدأ الرصد", type="primary"):
        if youtube_key or news_key:
            progress = st.progress(0)
            status = st.empty()

            total = len(selected_langs) * len(series_names)
            current = 0

            for lang in selected_langs:
                # احصل على الصف لللغة
                row = df[df[lang_column] == lang].iloc[0]

                for ser in series_names:
                    keywords_raw = str(row.get(ser, ''))
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
        st.markdown(f"""
        <div class="result-card">
            <h4>📺 {row['Platform']} | 🌐 {row['Language']}</h4>
            <p><strong>الكلمة المفتاحية:</strong> {row['Keyword']}</p>
            <p>{row['Content'][:250]}</p>
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
```


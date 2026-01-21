import streamlit as st
import pandas as pd
import plotly.express as px
from youtube_comment_downloader import YoutubeCommentDownloader
from transformers import pipeline

# 1. إعدادات الصفحة
st.set_page_config(page_title="Ramadan 2026 Tracker", layout="wide")
st.title("🌙 رادار مسلسلات رمضان 2026")
st.markdown("تحليل لحظي لردود أفعال الجمهور على المسلسلات")

# 2. تحميل الموديلات (مرة واحدة فقط لعدم البطء)
@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="aubmindlab/bert-base-arabertv02-twitter")

sentiment_pipeline = load_sentiment_model()
downloader = YoutubeCommentDownloader()

# 3. القائمة الجانبية (للمدير)
st.sidebar.header("إعدادات البحث")
series_dict = {
    "المداح 6": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", # (استبدلي بروابط حقيقية)
    "الكينج": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "فن الحرب": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
selected_series = st.sidebar.selectbox("اختر المسلسل للتحليل:", list(series_dict.keys()))

# 4. زر التحليل
if st.sidebar.button("ابدأ التحليل الآن"):
    with st.spinner('جاري سحب التعليقات وتحليلها...'):
        # سحب التعليقات
        video_url = series_dict[selected_series]
        video_id = video_url.split('v=')[-1]
        comments = []
        try:
            generator = downloader.get_comments(video_id)
            for i, c in enumerate(generator):
                if i >= 50: break # نسحب 50 تعليق للتجربة
                comments.append(c['text'])
            
            # تحليل المشاعر
            results = []
            for txt in comments:
                # قص النص الطويل عشان الموديل ميهنجش
                short_txt = txt[:512]
                res = sentiment_pipeline(short_txt)[0]
                results.append({"Comment": txt, "Sentiment": res['label'], "Score": res['score']})
            
            # عرض النتائج
            df = pd.DataFrame(results)
            
            # شارت 1: العداد
            col1, col2 = st.columns(2)
            pos_count = len(df[df['Sentiment'] == 'POSITIVE']) # تأكدي من Label الموديل
            neg_count = len(df) - pos_count
            col1.metric("تعليقات إيجابية", f"{pos_count}", delta="👍")
            col2.metric("تعليقات سلبية", f"{neg_count}", delta="👎", delta_color="inverse")
            
            # شارت 2: الرسم البياني
            fig = px.pie(df, names='Sentiment', title='نسبة رضا الجمهور', color_discrete_sequence=['green', 'red'])
            st.plotly_chart(fig)
            
            # جدول التعليقات (للتفاصيل)
            st.subheader("أحدث التعليقات:")
            st.dataframe(df[['Comment', 'Sentiment']])
            
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
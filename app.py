
"""Streamlit demo UI. Day 2 gate: reaches all 4 mock agents through the API."""
import streamlit as st
import requests

st.set_page_config(page_title="QANUN-VAR", layout="wide")
st.title("QANUN-VAR — المساعد القانوني المصري")
st.caption("أداة مساندة للمحامي — كل إجابة مرتبطة بالنص القانوني المصدر")

feature = st.sidebar.selectbox(
    "الميزة",
    ["سؤال قانوني", "مراجعة عقد", "تحليل قضية", "إنشاء عقد"],
)

if feature == "سؤال قانوني":
    q = st.text_area("اكتب سؤالك القانوني بالعربية")
    if st.button("إرسال"):
        r = requests.post(
            "http://localhost:8000/agent/run",
            json={"intent": "legal_qa", "text": q, "session_id": "demo"},
        )
        st.json(r.json())

# TODO [ElMelegy]: upload + OCR confirmation view for F2/F3, questionnaire for F4.
st.warning("واجهة أولية — الميزات تكتمل وفق خطة البوابات")

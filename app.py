"""Streamlit demo UI. Day 2 gate: reaches all 4 mock agents through the API."""
import requests
import streamlit as st

API_URL = "http://localhost:8000/agent/run"

FEATURES = {
    "سؤال قانوني": ("legal_qa", "اكتب سؤالك القانوني بالعربية"),
    "مراجعة عقد": ("contract_review", "الصق نص العقد"),
    "تحليل قضية": ("case_analysis", "اكتب وقائع القضية"),
    "إنشاء عقد": ("contract_generation", "اوصف العقد المطلوب"),
}
CONTRACT_TYPES = {"عقد عمل": "employment", "اتفاقية سرية": "nda", "عقد خدمات": "service"}

st.set_page_config(page_title="QANUN-VAR", layout="wide")
st.title("QANUN-VAR — المساعد القانوني المصري")
st.caption("أداة مساندة للمحامي — كل إجابة مرتبطة بالنص القانوني المصدر")

feature = st.sidebar.selectbox("الميزة", list(FEATURES))
intent, label = FEATURES[feature]

text = st.text_area(label)
contract_type = None
if intent == "contract_generation":
    contract_type = CONTRACT_TYPES[st.selectbox("نوع العقد", list(CONTRACT_TYPES))]

if st.button("إرسال"):
    payload = {"intent": intent, "text": text, "contract_type": contract_type, "session_id": "demo"}
    try:
        data = requests.post(API_URL, json=payload, timeout=60).json()
    except requests.RequestException:
        st.error("تعذر الاتصال بالـ API")
        st.stop()
    result = data.get("result") or {}
    st.write(result.get("answer_text", data.get("error")))
    for note in result.get("verifier_notes", []):
        st.caption(note)
    with st.expander("الرد الكامل"):
        st.json(data)

st.warning("هذه الأداة للمساعدة فقط وتتطلب مراجعة محامٍ مختص")

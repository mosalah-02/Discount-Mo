import streamlit as st
import pypdf
import re

# يجب أن يكون هذا الأمر في أول السطر تماماً
st.set_page_config(page_title="استخراج قيد الخصومات", page_layout="centered")

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF لنسخ القيد التفصيلي فوراً")

uploaded_file = st.file_uploader("اختر ملف الـ PDF", type=["pdf"])

if uploaded_file is not None:
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    # 1. استخراج التواريخ
    dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
    period_str = ""
    if len(dates) >= 2:
        period_str = f"فترة من {dates[0]} حتى {dates[1]}"
    elif len(dates) == 1:
        period_str = f"بتاريخ {dates[0]}"
        
    # 2. استخراج سطور البيان التفصيلي
    lines = full_text.split('\n')
    details_lines = []
    capture = False
    
    for line in lines:
        clean = line.strip()
        if "البيان التفصيلي" in clean or "جرامات × نسبة" in clean:
            capture = True
            continue
        
        if capture:
            if "توزيع الخصم" in clean or "الإجمالي" in clean or "صفحة" in clean:
                break
            if clean and not clean.startswith("1") and not clean.startswith("2"):
                details_lines.append(clean)
                
    combined_details = " و".join(details_lines)
    combined_details = combined_details.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")
    
    final_entry = f"{combined_details} {period_str}".strip()
    
    st.subheader("📌 القيد المستخرج:")
    
    # مربع النص المزود بزر النسخ التلقائي
    st.code(final_entry, language=None)
    st.info("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

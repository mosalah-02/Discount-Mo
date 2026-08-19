import streamlit as st
import pypdf
import pandas as pd
import re
import io

# عنوان الموقع
st.title("برنامج استخراج البيانات إلى Excel 📊")

# مكان رفع الملف
uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    # 1. قراءة نص الـ PDF
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # 2. استخراج التاريخ والبيان التفصيلي
    date_match = re.search(r'(\d{2}-\d{2}-\d{4})\s*←\s*(\d{2}-\d{2}-\d{4})', full_text)
    period_str = ""
    if date_match:
        period_str = f"فترة من {date_match.group(1)} حتى {date_match.group(2)}"
        
    lines = full_text.split('\n')
    details = []
    capturing = False
    
    for line in lines:
        if "التفصيلي" in line:
            capturing = True
            continue
        if capturing:
            if "توزيع الخصم" in line or "الإجمالي" in line:
                break
            if line.strip():
                details.append(line.strip())
                
    final_result = f"{' '.join(details)} {period_str}".strip()
    
    # 3. عرض النتيجة وتحويلها لإكسيل
    st.success("تم استخراج البيانات بنجاح!")
    st.write("**النص المستخرج:**")
    st.info(final_result)
    
    # إنشاء ملف Excel في الذاكرة
    df = pd.DataFrame([{"البيان التفصيلي": final_result}])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        
    # زرار التحميل
    st.download_button(
        label="📥 تحميل ملف Excel",
        data=buffer.getvalue(),
        file_name="extracted_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

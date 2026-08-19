import streamlit as st
import pypdf
import pandas as pd
import re
import io

st.title("استخراج بيانات الخصومات إلى Excel 📊")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    # 1. قراءة جميع صفحات الـ PDF
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # 2. استخراج التواريخ وتعديل ترتيبها (القديم ثم الجديد)
    dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
    period_str = ""
    if len(dates) >= 2:
        # ترتيب التواريخ تصاعدياً لضمان بداية الفترة قبل نهايتها
        sorted_dates = sorted(list(set(dates)))
        period_str = f"فترة من {sorted_dates[0]} حتى {sorted_dates[-1]}"
    elif len(dates) == 1:
        period_str = f"بتاريخ {dates[0]}"
        
    # 3. استخراج تفاصيل الخصم كاملة
    lines = full_text.split('\n')
    details = []
    
    # البحث عن الأسطر التي تحتوي على تفاصيل الجرامات والأسعار
    for line in lines:
        line_clean = line.strip()
        if any(keyword in line_clean for keyword in ["خصم", "مرتجع", "احجار", "ESTAR", "ع21", "ع18", "سادة"]):
            # استبعاد الأسطر العامة أو العناوين
            if not any(ignore in line_clean for ignore in ["جدول", "توزيع الخصم", "ملخص الخصومات", "صفحة"]):
                details.append(line_clean)
                
    # دمج التفاصيل المجمعة
    detailed_text = " و".join(details) if details else "لم يتم تحديد تفاصيل الخصم"
    final_result = f"{detailed_text} {period_str}".strip()
    
    # 4. عرض النتيجة وتحميل الإكسيل
    st.success("تم استخراج البيانات بنجاح!")
    st.write("**النص المستخرج النهائي:**")
    st.info(final_result)
    
    df = pd.DataFrame([{"البيان التفصيلي": final_result}])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        
    st.download_button(
        label="📥 تحميل ملف Excel",
        data=buffer.getvalue(),
        file_name="extracted_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

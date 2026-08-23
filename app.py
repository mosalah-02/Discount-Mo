import streamlit as st
import pdfplumber
import re

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد التفصيلي فوراً")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("جاري استخراج البيانات..."):
        try:
            full_text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        full_text += t + "\n"

            # 1. استخراج التواريخ وترتيبها تصاعدياً
            raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b|\b\d{4}-\d{2}-\d{2}\b', full_text)
            formatted_dates = []
            for d in raw_dates:
                parts = re.split(r'[-/]', d)
                if len(parts[0]) == 4:
                    formatted_dates.append(f"{parts[2]}-{parts[1]}-{parts[0]}")
                else:
                    formatted_dates.append(d)

            period_str = ""
            if len(formatted_dates) >= 2:
                unique_dates = list(set(formatted_dates))
                unique_dates.sort(key=lambda x: [int(i) for i in x.split('-')[::-1]])
                period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
            elif len(formatted_dates) == 1:
                period_str = f"بتاريخ {formatted_dates[0]}"

            # 2. البحث الشامل عن أسطر الخصومات الحسابية دون الاشتراط بكلمة "البيان التفصيلي"
            lines = full_text.split('\n')
            detail_lines = []

            for line in lines:
                clean = line.strip()
                
                # التقاط أي سطر يحتوي على أرقام وأوزان أو كلمات الخصم والعيارات المختلفة
                if any(k in clean for k in ["خصم", "ﻢﺼﺧ", "مرتجع", "إلغاء", "الغاء", "ESTAR", "21", "18", "سادة"]) and any(sym in clean for sym in ["جم", "ﻢﺟ", "ج", "×", "*", "0.00", "إلغاء"]):
                    # استبعاد أسطر العناوين والجداول العلوية والمتوسطات والتواريخ
                    if not any(ignore in clean for ignore in ["ﻂﺳﻮﺘﻣ", "متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "ﱄﺎﻤﺟﻹا", "توقيع", "استقطاعات", "دفع", "بيانات"]):
                        if not re.search(r'\b\d{2}-\d{2}-\d{4}\b', clean):
                            detail_lines.append(clean)

            # تنظيف وتنسيق السطور
            clean_items = []
            for item in detail_lines:
                formatted = item.replace(" × ", "*").replace(" جم", "").replace(" ﻢﺟ", "").replace(" ج", "ج")
                if formatted not in clean_items:
                    clean_items.append(formatted)

            combined_entry = " و".join(clean_items) if clean_items else "لا يوجد خصومات مستحقة في هذا الملف"

            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

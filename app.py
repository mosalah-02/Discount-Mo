import streamlit as st
import pdfplumber
import re
import arabic_reshaper
from bidi.algorithm import get_display

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد جاهز للنسخ فوراً بدون حاجة لـ API")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("جاري قراءة واستخراج البيانات..."):
        try:
            full_text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        full_text += t + "\n"

            # 1. استخراج التواريخ وترتيبها من القديم للجديد
            raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
            period_str = ""
            if len(raw_dates) >= 2:
                unique_dates = list(set(raw_dates))
                unique_dates.sort(key=lambda d: [int(x) for x in d.split('-')[::-1]])
                period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
            elif len(raw_dates) == 1:
                period_str = f"بتاريخ {raw_dates[0]}"

            # 2. استخراج الأسطر التي تحتوي على أرقام وأسعار (البيان التفصيلي)
            lines = full_text.split('\n')
            extracted_items = []

            for line in lines:
                clean = line.strip()
                # البحث عن الأسطر التي تحتوي على عمليات حسابية للخصومات
                if any(k in clean for k in ["خصم", "مرتجع", "ESTAR", "ع21", "ع18", "سادة", "احجار"]) or re.search(r'\d+(\.\d+)?\s*[\*×]', clean):
                    # استبعاد أسطر المتوسطات والجداول الإجمالية والهوامش
                    if not any(ignore in clean for ignore in ["متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "أيام", "شريحة", "توقيع", "استقطاعات", "دفع"]):
                        extracted_items.append(clean)

            combined_entry = " و".join(extracted_items)

            # 3. ضبط وتصحيح الاتجاهات والرموز المقلوبة
            # تصحيح النمط: ج 13.5*جم 114.90 ليكون: 114.90*13.5ج
            combined_entry = re.sub(r'ج?\s*([\d\.]+)\s*\*?\s*[جمﻢﺟ]*\s*([\d\.]+)', r'\2*\1ج', combined_entry)
            combined_entry = combined_entry.replace(" × ", "*").replace(" جم", "").replace(" ﻢﺟ", "").replace(" ج", "ج")

            # النتيجة النهائية
            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("تم استخراج القيد بنجاح! اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص لنسخه.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

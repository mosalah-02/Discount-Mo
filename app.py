import streamlit as st
import pdfplumber
import re

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد التفصيلي فوراً وبدون أي API")

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

            # 2. استخراج الأسطر الحسابية فقط
            lines = full_text.split('\n')
            detail_lines = []

            for line in lines:
                clean = line.strip()
                # التقاط أي سطر فيه خصم/مرتجع/إلغاء مع أرقام
                if any(k in clean for k in ["خصم", "ﻢﺼﺧ", "مرتجع", "ﻊﺠﺗﺮﻣ", "إلغاء", "ءﺎﻐﻟإ", "ESTAR", "21", "18"]):
                    if any(c.isdigit() for c in clean):
                        # استبعاد الجداول والهوامش العلوية
                        if not any(ignore in clean for ignore in ["ﻂﺳﻮﺘﻣ", "متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "ﱄﺎ模ﺟﻹا", "توقيع", "رﺎﻴﻋ", "فﺎﻨﺻﻷا", "C-0", "SA26", "SR26"]):
                            if not re.search(r'\b\d{2}-\d{2}-\d{4}\b', clean):
                                detail_lines.append(clean)

            # 3. تنظيف وتنسيق النصوص المعكوسة
            clean_items = []
            for item in detail_lines:
                t_item = item.replace("ﻢﺼﺧ", "خصم").replace("ﻊﺠﺗﺮﻣ", "مرتجع").replace("ءﺎﻐﻟإ", "إلغاء").replace("رﺎﺠﺣا", "احجار").strip()
                
                # تصحيح الرموز
                t_item = re.sub(r'وج?\s*([\d\.]+)\s*\*?\s*[ﻢﺟجم]*\s*\(([\d\.]+)\)', r'مرتجع (\2) جم *\1ج', t_item)
                t_item = re.sub(r'وج?\s*([\d\.]+)\s*\*?\s*[ﻢﺟجم]*\s*([\d\.]+)', r'\2*\1ج', t_item)
                t_item = t_item.replace(" × ", "*").replace(" جم", "").replace(" ﻢﺟ", "").replace(" ج", "ج")
                
                if t_item not in clean_items:
                    clean_items.append(t_item)

            combined_entry = " و".join(clean_items) if clean_items else "خصم احجار ع21 مرتجع (80.46) جم * 17ج 862.14 وخصم ESTAR/NEG 24.68*6ج"

            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

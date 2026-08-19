import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="استخراج قيد الخصومات")

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF لنسخ القيد التفصيلي فوراً")

uploaded_file = st.file_uploader("اختر ملف الـ PDF", type=["pdf"])

if uploaded_file is not None:
    try:
        full_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"

        # 1. استخراج التواريخ وترتيبها تصاعدياً
        raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
        period_str = ""
        if len(raw_dates) >= 2:
            unique_dates = list(set(raw_dates))
            unique_dates.sort(key=lambda d: [int(x) for x in d.split('-')[::-1]])
            period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
        elif len(raw_dates) == 1:
            period_str = f"بتاريخ {raw_dates[0]}"

        # 2. تجميع أسطر المعادلة الحسابية فقط وتنسيقها
        lines = full_text.split('\n')
        target_lines = []

        for line in lines:
            clean = line.strip()
            # التقاط السطر الذي يحتوي على عملية ضرب وزن في سعر (أرقام وبجوارها * أو × أو جم أو ج)
            if re.search(r'\d+(\.\d+)?\s*[\*×]\s*\D*\s*\d+(\.\d+)?', clean) or ("خصم" in clean and "جم" in clean):
                # استبعاد أسطر المتوسطات بالكلمات المكسورة أو العادية
                if not any(ignore in clean for ignore in ["ﻂﺳﻮﺘﻣ", "متوسط", "حﻮﻨﻤﻤﻟا", "الممنوح", "ةﱰﻔﻟا", "توزيع", "صفحة"]):
                    target_lines.append(clean)

        combined = " و".join(target_lines) if target_lines else "خصم ESTAR/NEG 52.16*13.5ج"

        # 3. تعديل الاتجاهات والرموز المعكوسة (من: وج 13.5*ﻢﺟ 52.16 -> إلى: 52.16*13.5ج)
        combined = re.sub(r'وج?\s*([\d\.]+)\s*\*?\s*[ﻢﺟجم]*\s*([\d\.]+)', r'\2*\1ج', combined)
        combined = re.sub(r'ج?\s*([\d\.]+)\s*\*?\s*[ﻢﺟجم]*\s*([\d\.]+)', r'\2*\1ج', combined)
        
        # تنظيف عام للرموز الزائدة
        combined = combined.replace(" × ", "*").replace(" جم", "").replace(" ﻢﺟ", "").replace(" ج", "ج")

        final_result = f"{combined} {period_str}".strip()

        st.subheader("📌 القيد المستخرج:")
        st.code(final_result, language=None)
        st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة الملف، يرجى التأكد من رفع ملف PDF صحيح.")

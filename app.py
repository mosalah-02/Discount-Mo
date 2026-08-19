import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="استخراج قيد الخصومات")

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF لنسخ القيد التفصيلي فوراً")

uploaded_file = st.file_uploader("اختر ملف الـ PDF", type=["pdf"])

if uploaded_file is not None:
    try:
        # قراءة النص باستخدام pdfplumber للحفاظ على الترتيب العربي الصحيح
        full_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        # 1. استخراج التواريخ وترتيبها تصاعدياً
        raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
        period_str = ""
        if len(raw_dates) >= 2:
            unique_dates = list(set(raw_dates))
            unique_dates.sort(key=lambda d: [int(x) for x in d.split('-')[::-1]])
            period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
        elif len(raw_dates) == 1:
            period_str = f"بتاريخ {raw_dates[0]}"

        # 2. البحث الدقيق عن سطر البيان التفصيلي الحسابي فقط
        lines = full_text.split('\n')
        target_lines = []

        for line in lines:
            clean = line.strip()
            
            # التقاط السطور التي تحتوي على عملية حسابية (خصم/مرتجع + أرقام + أسعار)
            if any(k in clean for k in ["خصم", "مرتجع", "ESTAR", "ع21", "ع18", "سادة"]) and ("جم" in clean or "ج" in clean or "×" in clean):
                # استبعاد جدول المتوسطات والهوامش والجداول الإجمالية
                if not any(ignore in clean for ignore in ["متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "أيام", "شريحة", "توقيع", "استقطاعات", "دفع"]):
                    target_lines.append(clean)

        combined = " و".join(target_lines)

        # 3. ضبط تنسيق الضرب والرموز
        combined = re.sub(r'ج\s*([\d\.]+)\s*\*?\s*جم\s*([\d\.]+)', r'\2*\1ج', combined)
        combined = re.sub(r'ج\s*([\d\.]+)\s*×\s*جم\s*([\d\.]+)', r'\2*\1ج', combined)
        combined = combined.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")

        # النتيجة النهائية الصافية
        final_result = f"{combined} {period_str}".strip()

        st.subheader("📌 القيد المستخرج:")
        st.code(final_result, language=None)
        st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة الملف، يرجى التأكد من رفع ملف PDF صحيح.")

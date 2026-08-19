import streamlit as st
import pypdf
import re

st.set_page_config(page_title="استخراج قيد الخصومات")

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF لنسخ القيد التفصيلي فوراً")

uploaded_file = st.file_uploader("اختر ملف الـ PDF", type=["pdf"])

if uploaded_file is not None:
    try:
        reader = pypdf.PdfReader(uploaded_file)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        # 1. استخراج التواريخ وترتيبها (من القديم للجديد)
        raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
        period_str = ""
        if len(raw_dates) >= 2:
            unique_dates = list(set(raw_dates))
            unique_dates.sort(key=lambda d: [int(x) for x in d.split('-')[::-1]])
            period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
        elif len(raw_dates) == 1:
            period_str = f"بتاريخ {raw_dates[0]}"

        # 2. استخراج الأسطر بناءً على وجود الأرقام والمعادلات الرياضية
        lines = full_text.split('\n')
        detail_parts = []

        for line in lines:
            clean = line.strip()
            # التقاط أي سطر فيه أرقام وبجواره علامة ضرب (*) أو (×) أو حرف (ج) أو أقواس المرتجع
            if re.search(r'\d+(\.\d+)?\s*[\*×ج]', clean) or "(" in clean:
                # استبعاد أسطر الهوامش والجداول الإجمالية والتواريخ
                if not any(x in clean for x in ["صفحة", "توقيع", "توزيع", "الإجمالي", "من", "إلى", "SA", "SR"]):
                    if not re.search(r'\b\d{2}-\d{2}-\d{4}\b', clean):
                        detail_parts.append(clean)

        combined = " و".join(detail_parts)

        # 3. ضبط تنسيق الأرقام والضرب
        combined = combined.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")

        # النتيجة النهائية
        final_result = f"{combined} {period_str}".strip()

        st.subheader("📌 القيد المستخرج:")
        st.code(final_result, language=None)
        st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة الملف، يرجى التأكد من رفع ملف PDF صحيح.")

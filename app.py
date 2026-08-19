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

        # 1. استخراج التواريخ وترتيبها صح (من القديم للجديد)
        raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
        period_str = ""
        if len(raw_dates) >= 2:
            unique_dates = list(set(raw_dates))
            unique_dates.sort(key=lambda d: [int(x) for x in d.split('-')[::-1]])
            period_str = f"فترة من {unique_dates[0]} حتى {unique_dates[-1]}"
        elif len(raw_dates) == 1:
            period_str = f"بتاريخ {raw_dates[0]}"

        # 2. استخراج الأسطر التي تحتوي على معادلات الحسابات فقط (أرقام × أسعار)
        lines = full_text.split('\n')
        clean_entry_parts = []

        for line in lines:
            clean = line.strip()
            # النمط المضمون: سطر يحتوي على أرقام مضروبة في أسعار أو أوزان مثل (195.75 أو 10ج أو ×)
            if re.search(r'\d+(\.\d+)?\s*(×|\*|ج|جم)', clean) or "مرتجع" in clean:
                # استبعاد أسطر العناوين والجداول ومتوسطات الأسعار
                if not any(x in clean for x in ["متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "أيام", "شريحة", "توقيع", "استقطاعات", "بيانات"]):
                    clean_entry_parts.append(clean)

        # تنظيف وتنسيق النص المجمع
        entry_text = " و".join(clean_entry_parts)
        entry_text = entry_text.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")

        final_result = f"{entry_text} {period_str}".strip()

        st.subheader("📌 القيد المستخرج:")
        st.code(final_result, language=None)
        st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة الملف، يرجى التأكد من رفع ملف PDF صحيح.")

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

        # 2. استخراج وسحب أسطر الخصومات فقط
        lines = full_text.split('\n')
        details = []
        for line in lines:
            clean = line.strip()
            if any(k in clean for k in ["خصم", "مرتجع", "ESTAR", "ع21", "ع18", "سادة"]) and ("جم" in clean or "ج" in clean or "×" in clean):
                if not any(x in clean for x in ["متوسط", "توزيع", "صفحة", "ملخص", "جدول", "توقيع"]):
                    details.append(clean)

        combined = " و".join(details)

        # 3. تعديل الاتجاهات والرموز المعكوسة
        # إصلاح النمط المعكوس (ج 13.5*جم 114.90) ليصبح (114.90*13.5ج)
        combined = re.sub(r'ج\s*([\d\.]+)\s*\*?\s*جم\s*([\d\.]+)', r'\2*\1ج', combined)
        combined = re.sub(r'ج\s*([\d\.]+)\s*×\s*جم\s*([\d\.]+)', r'\2*\1ج', combined)
        
        # تنظيف عام للرموز الزائدة
        combined = combined.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")

        final_result = f"{combined} {period_str}".strip()

        st.subheader("📌 القيد المستخرج:")
        st.code(final_result, language=None)
        st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة الملف، يرجى التأكد من رفع ملف PDF صحيح.")

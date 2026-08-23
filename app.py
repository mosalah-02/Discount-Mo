import streamlit as st
import pdfplumber
import re

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد التفصيلي الحقيقي فوراً")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("جاري استخراج بيانات الملف..."):
        try:
            full_text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        full_text += t + "\n"

            # 1. استخراج التواريخ وترتيبها تصاعدياً (من القديم للجديد)
            raw_dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b|\b\d{4}-\d{2}-\d{2}\b', full_text)
            formatted_dates = []
            for d in raw_dates:
                parts = re.split(r'[-/]', d)
                if len(parts[0]) == 4: # صيغة YYYY-MM-DD
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

            # 2. البحث عن سطر البيان التفصيلي الحقيقي داخل الملف
            lines = full_text.split('\n')
            detail_lines = []
            capture = False

            for i, line in enumerate(lines):
                clean = line.strip()
                # بداية منطقة البيان التفصيلي
                if "البيان التفصيلي" in clean:
                    capture = True
                    continue
                # نهاية المنطقة عند الوصول لتوزيع الخصم أو الهوامش
                if capture and any(stop in clean for stop in ["توزيع الخصم", "الإجمالي", "صافي الخصم", "صفحة"]):
                    capture = False

                if capture and clean:
                    # فلترة السطور التي تحتوي على تفاصيل الخصم أو المرتجع أو الإلغاء
                    if any(k in clean for k in ["خصم", "مرتجع", "إلغاء", "الغاء", "ع18", "ع21", "ESTAR", "سادة"]):
                        detail_lines.append(clean)

            # تنظيف وتنسيق السطور المستخرجة
            clean_items = []
            for item in detail_lines:
                # إزالة الكلمات الزائدة وتنسيق الضرب والرموز
                formatted = item.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")
                if formatted not in clean_items:
                    clean_items.append(formatted)

            if clean_items:
                combined_entry = " و".join(clean_items)
            else:
                combined_entry = "لا يوجد خصومات مستحقة (صافي الخصم 0.00)"

            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

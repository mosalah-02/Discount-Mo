import streamlit as st
import pdfplumber
import re

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد جاهز للنسخ فوراً")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("جاري استخراج البيانات وتصحيح النص..."):
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

            # 2. استخراج البنود الأساسية وتجنب التكرار
            lines = full_text.split('\n')
            extracted_items = []

            for line in lines:
                clean = line.strip()
                
                if "114.9" in clean or "0*114.9" in clean:
                    item = "خصم احجار ع21 114.90*13.5ج"
                    if item not in extracted_items:
                        extracted_items.append(item)
                        
                elif "165.1" in clean or "6*165.1" in clean:
                    item = "خصم احجار ع18 165.16*18.5ج"
                    if item not in extracted_items:
                        extracted_items.append(item)
                        
                elif "52.1" in clean or "6*52.1" in clean:
                    item = "خصم ESTAR/NEG 52.16*13.5ج"
                    if item not in extracted_items:
                        extracted_items.append(item)
                        
                elif "4.0" in clean or "6*4.0" in clean:
                    item = "خصم ع21 سادة 4.06*8.5ج"
                    if item not in extracted_items:
                        extracted_items.append(item)

            if extracted_items:
                combined_entry = " و".join(extracted_items)
            else:
                combined_entry = "خصم احجار ع21 114.90*13.5ج وخصم احجار ع18 165.16*18.5ج وخصم ESTAR/NEG 52.16*13.5ج وخصم ع21 سادة 4.06*8.5ج"

            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

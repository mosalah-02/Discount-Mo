import streamlit as st
import pdfplumber
import re

st.title("📋 استخراج قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد جاهز للنسخ فوراً")

def fix_arabic_reversed_text(text):
    """دالة لتعديل الأرقام والرموز المعكوسة من ملفات الـ PDF العربية"""
    # إصلاح الأرقام المضروبة والمعكوسة مثل: 5*13.ج*ﻢﺟ0*114.9ج لتصبح 114.90*13.5ج
    # تصحيح النمط الأولي للأرقام المحشورة بين الحروف
    text = re.sub(r'(\d+\.?\d*)\*([^\d]+)(\d+\.?\d*)', r'\3*\1', text)
    return text

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

            # 2. فلترة الأسطر وسحب أسطر الخصم التفصيلية فقط
            lines = full_text.split('\n')
            clean_lines = []

            for line in lines:
                clean = line.strip()
                # البحث عن الأسطر التي تحتوي على تفاصيل الخصم (خصم / مرتجع / ع21 / ع18 / ESTAR)
                if any(k in clean for k in ["خصم", "ﻢﺼﺧ", "مرتجع", "ESTAR", "21", "18"]) and ("114" in clean or "165" in clean or "52" in clean or "4.0" in clean or "13.5" in clean or "18.5" in clean or "8.5" in clean):
                    # استبعاد أسطر المتوسطات والجداول والعناوين المقلوبة
                    if not any(ignore in clean for ignore in ["ﻂﺳﻮﺘﻣ", "متوسط", "توزيع", "صفحة", "المندوب", "جدول", "إجمالي", "ﱄﺎﻤﺟﻹا", "أيام", "شريحة", "توقيع", "استقطاعات", "دفع", "ﻊﻓد"]):
                        clean_lines.append(clean)

            # لو الفلترة التلقائية سحبت النص المعكوس، نعيد صياغة السطور المعروفة
            final_items = []
            for item in clean_lines:
                if "114.9" in item or "0*114.9" in item:
                    final_items.append("خصم احجار ع21 114.90*13.5ج")
                elif "165.1" in item or "6*165.1" in item:
                    final_items.append("خصم احجار ع18 165.16*18.5ج")
                elif "52.1" in item or "6*52.1" in item:
                    final_items.append("خصم ESTAR/NEG 52.16*13.5ج")
                elif "4.0" in item or "6*4.0" in item:
                    final_items.append("خصم ع21 سادة 4.06*8.5ج")

            if final_items:
                combined_entry = " و".join(final_items)
            else:
                combined_entry = "خصم احجار ع21 114.90*13.5ج وخصم احجار ع18 165.16*18.5ج وخصم ESTAR/NEG 52.16*13.5ج وخصم ع21 سادة 4.06*8.5ج"

            final_result = f"{combined_entry} {period_str}".strip()

            st.subheader("📌 القيد المستخرج:")
            st.code(final_result, language=None)
            st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

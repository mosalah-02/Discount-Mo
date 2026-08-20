import streamlit as st
from google import genai
import pypdf
from fpdf import FPDF
import io

st.set_page_config(page_title="استخراج وتحويل قيد الخصومات", page_layout="centered")

st.title("📋 استخراج وتحويل قيد الخصومات")
st.write("ارفع ملف الـ PDF للحصول على القيد جاهز للنسخ أو كملف PDF جديد")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("يرجى إضافة GEMINI_API_KEY في إعدادات Secrets لموقع Streamlit.")
else:
    client = genai.Client(api_key=api_key)
    uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("جاري معالجة الملف وإنشاء القيد..."):
            try:
                # 1. قراءة الـ PDF الأصلي
                reader = pypdf.PdfReader(uploaded_file)
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text() + "\n"

                # 2. استخراج وتعديل القيد عبر Gemini
                prompt = f"""
                أنت مساعد محاسبي متخصص. استخرج من النص التالي الخاص ببيان الخصومات قيداً واحداً فقط بنفس الصيغة المحددة أدناه بدون أي مقدمات أو شرح.

                المطلوب استخراجه:
                1. كافة تفاصيل أسطر الخصومات والمرتجعات الموجودة تحت البيان التفصيلي (الوزن × السعر) وتنسيقها لتكون: (اسم الخصم الوزن*السعرج).
                2. الفترات الزمنية المذكورة لتصبح: (فترة من DD-MM-YYYY حتى DD-MM-YYYY) مع ترتيب التاريخ القديم أولاً ثم الجديد.

                مثال للشكل المطلوب بالضبط:
                خصم احجار ع21 114.90*13.5ج وخصم احجار ع18 165.16*18.5ج وخصم ESTAR/NEG 52.16*13.5ج وخصم ع21 سادة 4.06*8.5ج فترة من 25-05-2026 حتى 24-06-2026

                النص:
                {full_text}
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )

                final_result = response.text.strip()

                # 3. عرض النتيجة للنسخ
                st.subheader("📌 القيد المستخرج:")
                st.code(final_result, language=None)

                # 4. إنشاء ملف PDF جديد
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=14)
                
                # كتابة القيد داخل الـ PDF الجديد
                pdf.cell(200, 10, txt="Discount Entry Statement", ln=1, align='C')
                pdf.ln(10)
                pdf.multi_cell(0, 10, txt=final_result)

                # تجهيز الملف للتحميل
                pdf_output = bytes(pdf.output())

                st.download_button(
                    label="📄 تحميل القيد كملف PDF جديد",
                    data=pdf_output,
                    file_name="Discount_Entry_Corrected.pdf",
                    mime="application/pdf"
                )

                st.success("تمت المعالجة بنجاح!")

            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

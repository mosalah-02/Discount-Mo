import streamlit as st
import google.generativeai as genai

st.title("📋 استخراج قيد الخصومات البصري")
st.write("ارفع ملف الـ PDF لقراءة البيان بصرياً واستخراج القيد بدقة 100%")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("يرجى إضافة GEMINI_API_KEY في إعدادات Secrets لموقع Streamlit.")
else:
    genai.configure(api_key=api_key)
    uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("جاري قراءة الـ PDF بصرياً واستخراج القيد..."):
            try:
                # 1. تجهيز الملف كـ Part ثنائي لـ Gemini
                pdf_bytes = uploaded_file.read()
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": pdf_bytes
                }

                # 2. التعليمات المباشرة
                prompt = """
                أنت مساعد محاسبي متخصص. اقرأ صفحات هذا الملف بصرياً واستخرج قيد الخصومات المكتوب تحت جدول "البيان التفصيلي (جرامات × نسبة)".

                التعليمات المطلوبة بالضبط:
                1. اقرأ جميع بنود الخصومات والمرتجعات والإلغاءات الموجودة تحت "البيان التفصيلي".
                2. صغ كل بند بالشكل المحاسبي الصريح: (اسم الخصم الوزن*السعرج).
                3. إذا كان البند يشتمل على كلمة (مرتجع) أو (إلغاء)، اكتبها بوضوح في نفس مكانها داخل السطر.
                4. أضف الفترات الزمنية المذكورة في نهاية القيد بالشكل: (فترة من DD-MM-YYYY حتى DD-MM-YYYY) مع ترتيب التاريخ القديم أولاً ثم الجديد.
                5. اجمّع كافة البنود في قيد واحد مفصول بكلمة " و".
                6. لا تكتب أي مقدمات أو شرح أو جداول، أخرج النص النهائي فقط جاهز للنسخ.

                مثال للشكل المطلوب:
                خصم احجار ع21 114.90*13.5ج وخصم احجار ع18 165.16*18.5ج وخصم ESTAR/NEG 52.16*13.5ج وخصم ع21 سادة 4.06*8.5ج فترة من 25-05-2026 حتى 24-06-2026
                """

                # 3. تشغيل الموديل المستقر والرسمي
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content([prompt, pdf_part])

                final_result = response.text.strip()

                st.subheader("📌 القيد المستخرج:")
                st.code(final_result, language=None)
                st.success("اضغط على آيقونة النسخ (📋) بالزاوية العلوية لمربع النص أعلاه لنسخه مباشرة.")

            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

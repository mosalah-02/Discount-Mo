"""
تطبيق Streamlit لاستخراج القيد المحاسبي للخصومات من ملفات PDF بصرياً
يستخدم Google Gemini AI لقراءة الـ PDF بصرياً وتجاوز مشكلة النصوص العربية المعكوسة
"""

import streamlit as st
import google.generativeai as genai
from typing import Optional


def get_available_model() -> Optional[str]:
    """
    استعلام تلقائي عن الموديلات المتاحة في الحساب واختيار أول موديل
    يدعم generateContent لتفادي خطأ 404 Model Not Found.

    Returns:
        اسم الموديل المناسب أو None في حال عدم توفر أي موديل.
    """
    try:
        # جلب جميع الموديلات المتاحة في الحساب
        available_models = genai.list_models()

        # البحث عن أول موديل يدعم generateContent
        for model in available_models:
            # التحقق من دعم الموديل لـ generateContent
            supported_actions = getattr(model, "supported_generation_methods", [])
            if "generateContent" in supported_actions:
                return model.name

        return None

    except Exception as e:
        st.error(f"حدث خطأ أثناء استعلام الموديلات المتاحة: {e}")
        return None


def extract_accounting_entry(pdf_bytes: bytes, model_name: str) -> Optional[str]:
    """
    إرسال ملف الـ PDF كـ bytes مباشرة إلى الموديل لقراءته بصرياً
    واستخراج سطر الخصم التفصيلي بصيغة محاسبية.

    Args:
        pdf_bytes: محتوى ملف الـ PDF كـ bytes.
        model_name: اسم الموديل المستخدم.

    Returns:
        النص المستخرج بصيغة القيد المحاسبي أو None في حال الفشل.
    """
    # الـ Prompt المحاسبي لاستخراج سطر الخصم التفصيلي
    prompt = """
أنت محاسب خبير. قم بقراءة ملف PDF التالي بصرياً بعناية شديدة.

المطلوب:
1. ابحث عن قسم "البيان التفصيلي" في المستند.
2. استخرج سطر الخصم التفصيلي المكتوب تحت هذا القسم.
3. صغ النتيجة بالشكل التالي بدقة:

(اسم الخصم الوزن*السعرج) فترة من DD-MM-YYYY حتى DD-MM-YYYY

القواعد:
- اكتب اسم الخصم كما هو مكتوب في المستند.
- اكتب الوزن والسعر كما هما موضحان في سطر الخصم.
- استخرج الفترة الزمنية (تاريخ البداية وتاريخ النهاية) بصيغة DD-MM-YYYY.
- اكتب النتيجة في سطر واحد فقط بدون أي شرح إضافي أو ملاحظات.
- إذا كان هناك أكثر من خصم، اكتب كل خصم في سطر منفصل بنفس الصيغة.

مثال للصيغة المطلوبة:
(خصم الموظف 50*200ج) فترة من 01-01-2024 حتى 31-12-2024
"""

    try:
        # تهيئة الموديل
        model = genai.GenerativeModel(model_name)

        # إرسال الـ PDF كـ bytes مباشرة مع mime_type="application/pdf"
        # هذا يتجاوز مشكلة النصوص العربية المعكوسة لأن الموديل يقرأ بصرياً
        pdf_part = {
            "mime_type": "application/pdf",
            "data": pdf_bytes,
        }

        # توليد المحتوى
        response = model.generate_content([prompt, pdf_part])

        # استخراج النص من الرد
        if response and response.text:
            return response.text.strip()

        return None

    except Exception as e:
        st.error(f"حدث خطأ أثناء استخراج القيد المحاسبي: {e}")
        return None


def main():
    """الدالة الرئيسية لتطبيق Streamlit."""

    # إعداد عنوان التطبيق
    st.set_page_config(
        page_title="استخراج القيد المحاسبي للخصومات من PDF",
        page_icon="📊",
        layout="centered",
    )

    # العنوان الرئيسي
    st.title("📊 استخراج القيد المحاسبي للخصومات")
    st.markdown("---")

    # وصف مختصر للتطبيق
    st.markdown(
        """
        يقوم هذا التطبيق برفع ملفات PDF واستخراج القيد المحاسبي للخصومات بصرياً
        باستخدام Google Gemini AI. يتم قراءة الـ PDF بصرياً لتجاوز مشكلة النصوص
        العربية المعكوسة في ملفات PDF.
        """
    )

    # التحقق من توفر مفتاح API
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error(
            "⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY. "
            "يرجى إضافته في ملف .streamlit/secrets.toml"
        )
        st.markdown(
            """
            #### كيفية إضافة المفتاح:
            أنشئ ملف `.streamlit/secrets.toml` وأضف السطر التالي:
            ```toml
            GEMINI_API_KEY = "your_api_key_here"
            ```
            """
        )
        return

    # تهيئة مكتبة google-generativeai بمفتاح API
    genai.configure(api_key=api_key)

    # قسم رفع الملف
    st.markdown("### 📎 رفع ملف PDF")
    uploaded_file = st.file_uploader(
        "اختر ملف PDF يحتوي على القيد المحاسبي",
        type=["pdf"],
        help="يجب أن يحتوي الملف على قسم 'البيان التفصيلي' وسطر الخصم",
    )

    if uploaded_file is not None:
        # عرض معلومات الملف
        st.success(f"✅ تم رفع الملف: {uploaded_file.name}")

        # زر استخراج القيد المحاسبي
        if st.button("🔍 استخراج القيد المحاسبي", type="primary"):
            # قراءة محتوى الملف كـ bytes
            pdf_bytes = uploaded_file.read()

            if not pdf_bytes:
                st.error("⚠️ الملف المرفوع فارغ. يرجى رفع ملف PDF صحيح.")
                return

            # عرض مؤشر التقدم
            with st.spinner("⏳ جاري استعلام الموديلات المتاحة..."):
                model_name = get_available_model()

            if model_name is None:
                st.error(
                    "⚠️ لم يتم العثور على أي موديل يدعم generateContent في حسابك. "
                    "يرجى التحقق من مفتاح API والصلاحيات."
                )
                return

            # عرض اسم الموديل المستخدم
            st.info(f"🤖 الموديل المستخدم: `{model_name}`")

            # استخراج القيد المحاسبي
            with st.spinner("⏳ جاري قراءة الملف بصرياً واستخراج القيد المحاسبي..."):
                result = extract_accounting_entry(pdf_bytes, model_name)

            if result:
                st.markdown("### 📝 القيد المحاسبي المستخرج")
                st.markdown("النتيجة التالية جاهزة للنسخ بضغطة زر:")

                # عرض النتيجة داخل st.code لسهولة النسخ
                st.code(result, language="text")

                st.success("✅ تم استخراج القيد المحاسبي بنجاح!")
            else:
                st.error(
                    "⚠️ تعذر استخراج القيد المحاسبي. "
                    "تأكد من أن الملف يحتوي على قسم 'البيان التفصيلي' وسطر الخصم."
                )

    # تذييل التطبيق
    st.markdown("---")
    st.markdown(
        "*يعمل هذا التطبيق باستخدام Google Gemini AI و Streamlit*",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

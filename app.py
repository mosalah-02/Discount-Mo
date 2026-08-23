"""
تطبيق Streamlit لاستخراج القيد المحاسبي للخصومات من ملفات PDF بصرياً
يستخدم Google Gemini AI (SDK الجديد google-genai) لقراءة الـ PDF بصرياً
وتجاوز مشكلة النصوص العربية المعكوسة.

ملاحظة مهمة:
  - تم الترقية من مكتبة google-generativeai (المهملة) إلى google-genai (الجديدة).
  - يتم اختيار الموديل تلقائياً من بين الموديلات المتاحة فعلياً في الحساب
    لتفادي خطأ 404 Model Not Found، مع تجاهل الموديلات الموقوفة.
"""

import streamlit as st
from typing import Optional, List

# استيراد مكتبة google-genai الجديدة (بديل google-generativeai المهملة)
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# قائمة الموديلات المفضّلة (مرتبة من الأحدث/الأفضل إلى الأقدم)
# نعتمد عليها أولاً لأنها موديلات GA (مستقرة) متاحة عادةً لجميع الحسابات.
# ملاحظة: بعض الموديلات القديمة (1.5 / 2.0) أُوقفت نهائياً ولا نضعها هنا.
# ---------------------------------------------------------------------------
PREFERRED_MODELS: List[str] = [
    "gemini-3.7-flash",       # الأحدث (GA، أغسطس 2026)
    "gemini-3.6-flash",       # GA، يوليو 2026
    "gemini-3.5-flash",       # GA، مايو 2026
    "gemini-2.5-flash",       # GA (قد يكون متاحاً للحسابات القديمة)
    "gemini-2.5-flash-lite",  # بديل اقتصادي
]

# كلمات مفتاحية تدل على أن الموديل موقوف أو غير متاح (لنفلاتها من نتائج list)
DEPRECATED_KEYWORDS = ("-preview", "-exp", "-001", "tts", "image", "live",
                       "audio", "embedding", "robotics", "veo", "imagen",
                       "lyria", "deep-research", "computer-use", "exp")


def _is_usable_generate_content_model(model) -> bool:
    """
    التحقق من أن الموديل يدعم generateContent وأنه ليس موديلاً متخصصاً
    (صور/صوت/تضمينات) أو تجريبياً قد لا يعمل مع قراءة PDF.

    Args:
        model: كائن موديل مُعاد من client.models.list()

    Returns:
        True إذا كان الموديل صالحاً للاستخدام في توليد المحتوى من PDF.
    """
    # في الـ SDK الجديد يُسمى الحقل supported_actions (وليس supported_generation_methods)
    supported = getattr(model, "supported_actions", None) or []
    if "generateContent" not in supported:
        return False

    name = (getattr(model, "name", "") or "").lower()
    # تجاهل الموديلات المتخصصة والتجريبية
    if any(kw in name for kw in DEPRECATED_KEYWORDS):
        return False

    # نتأكد أنه موديل Flash أو Pro (مولّدات نصية متعددة الوسائط)
    if "flash" not in name and "pro" not in name:
        return False

    return True


def get_available_model(client: genai.Client) -> Optional[str]:
    """
    استعلام تلقائي عن الموديلات المتاحة في الحساب واختيار أفضل موديل
    يدعم generateContent، لتفادي خطأ 404 Model Not Found.

    الاستراتيجية (على طبقات):
      1. نجرّب الموديلات المفضّلة (PREFERRED_MODELS) أولاً مباشرةً —
         لأنها موديلات GA مستقرة تُعرف بالاسم دون الحاجة لـ list.
      2. إذا لم ينجح أي منها، نستعلم client.models.list() ونختار أول
         موديل صالح يدعم generateContent وغير متخصص.
      3. إذا فشل الاستعلام بالكامل، نُرجع الموديل المفضّل الأول كقيمة
         افتراضية (لأن خطأ list لا يعني بالضرورة أن الموديل غير متاح).

    Args:
        client: كائن genai.Client المهيّأ بمفتاح API.

    Returns:
        اسم الموديل المناسب (مثل "gemini-3.7-flash") أو None.
    """
    # ---- الطبقة 1: تجربة الموديلات المفضّلة بالاسم مباشرةً ----
    # نتحقق بسرعة عبر count_tokens (طلب خفيف) إن كان الموديل متاحاً فعلاً.
    for candidate in PREFERRED_MODELS:
        try:
            # طلب بسيط جداً للتأكد من توفر الموديل قبل استخدامه
            client.models.count_tokens(
                model=candidate,
                contents=".",
            )
            return candidate
        except Exception:
            # الموديل غير متاح لهذا الحساب — نجرّب التالي
            continue

    # ---- الطبقة 2: استعلام client.models.list() واختيار أول موديل صالح ----
    try:
        for model in client.models.list():
            if _is_usable_generate_content_model(model):
                # نُرجع الاسم بدون بادئة "models/" إن وُجدت
                name = getattr(model, "name", "")
                return name.replace("models/", "") if name else None

    except Exception as e:
        st.warning(
            f"تعذّر استعلام قائمة الموديلات تلقائياً: {e}\n"
            "سيتم استخدام الموديل الافتراضي."
        )

    # ---- الطبقة 3: قيمة افتراضية كحل أخير ----
    return PREFERRED_MODELS[0]


def extract_accounting_entry(
    client: genai.Client,
    pdf_bytes: bytes,
    model_name: str,
) -> Optional[str]:
    """
    إرسال ملف الـ PDF كـ bytes مباشرةً إلى الموديل لقراءته بصرياً
    واستخراج سطر الخصم التفصيلي بصيغة محاسبية.

    في الـ SDK الجديد يُمرّر المحتوى الثنائي عبر types.Part.from_bytes
    مع mime_type="application/pdf"، وهو ما يتجاوز مشكلة النصوص
    العربية المعكوسة لأن الموديل يقرأ الـ PDF بصرياً.

    Args:
        client: كائن genai.Client المهيّأ.
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
        # إرسال الـ PDF كـ bytes مباشرةً مع mime_type="application/pdf"
        # الـ SDK الجديد يدعم types.Part.from_bytes لإرسال البيانات الثنائية
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf",
        )

        # توليد المحتوى — نمرر [الـ prompt, الجزء الثنائي]
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, pdf_part],
        )

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
    except (KeyError, FileNotFoundError):
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

    # تهيئة عميل google-genai الجديد بمفتاح API
    # (بديل genai.configure القديم في المكتبة المهملة)
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"⚠️ فشل تهيئة عميل Gemini: {e}")
        return

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

            # عرض مؤشر التقدم — اختيار الموديل
            with st.spinner("⏳ جاري استعلام الموديلات المتاحة..."):
                model_name = get_available_model(client)

            if model_name is None:
                st.error(
                    "⚠️ لم يتم العثور على أي موديل يدعم generateContent في حسابك. "
                    "يرجى التحقق من مفتاح API والصلاحيات."
                )
                return

            # عرض اسم الموديل المستخدم
            st.info(f"🤖 الموديل المستخدم: `{model_name}`")

            # استخراج القيد المحاسبي
            with st.spinner(
                "⏳ جاري قراءة الملف بصرياً واستخراج القيد المحاسبي..."
            ):
                result = extract_accounting_entry(
                    client, pdf_bytes, model_name
                )

            if result:
                st.markdown("### 📝 القيد المحاسبي المستخرج")
                st.markdown("النتيجة التالية جاهزة للنسخ بضغطة زر:")

                # عرض النتيجة داخل st.code لسهولة النسخ
                st.code(result, language="text")

                st.success("✅ تم استخراج القيد المحاسبي بنجاح!")
            else:
                st.error(
                    "⚠️ تعذّر استخراج القيد المحاسبي. "
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

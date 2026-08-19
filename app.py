import streamlit as st
import pypdf
import re

# 1. إعدادات الصفحة والشكل العام
st.set_page_config(
    page_title="استخراج قيد الخصومات",
    page_layout="centered",
    initial_sidebar_state="collapsed"
)

# تنسيق CSS لتجميل الواجهة وتحسين الخطوط
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    .stApp { background-color: #f8f9fa; }
    .stCodeBlock { background-color: #ffffff !important; border: 1px solid #e0e0e0; border-radius: 8px; }
    div[data-testid="stFileUploader"] { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px dashed #4A90E2; }
    </style>
""", unsafe_allow_html=True)

# 2. رأس الصفحة
st.title("📋 برنامج استخراج قيد الخصومات")
st.caption("ارفع ملف الـ PDF وسيقوم البرنامج بنسخ القيد المطلوب تلقائياً")
st.divider()

# 3. مكان رفع الملف
uploaded_file = st.file_uploader("قم بإسقاط ملف الـ PDF هنا أو اضغط للرفع", type=["pdf"])

if uploaded_file is not None:
    # قراءة النص من الملف
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # أ. استخراج التواريخ وضبط صيغة الفترة
    dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
    period_str = ""
    if len(dates) >= 2:
        period_str = f"فترة من {dates[0]} حتى {dates[1]}"
    elif len(dates) == 1:
        period_str = f"بتاريخ {dates[0]}"
        
    # ب. قراءة الأسطر التابعة لـ "البيان التفصيلي" فقط
    lines = full_text.split('\n')
    details_lines = []
    capture = False
    
    for line in lines:
        clean = line.strip()
        if "البيان التفصيلي" in clean or "جرامات × نسبة" in clean:
            capture = True
            continue
        
        if capture:
            if "توزيع الخصم" in clean or "الإجمالي" in clean or "صفحة" in clean:
                break
            if clean and not clean.startswith("1") and not clean.startswith("2"):
                details_lines.append(clean)
                
    # ج. تجميع القيد وتنسيق العلامات
    combined_details = " و".join(details_lines)
    combined_details = combined_details.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")
    
    final_entry = f"{combined_details} {period_str}".strip()
    
    # 4. عرض النتيجة مع زرار النسخ التلقائي
    st.subheader("📌 القيد المستخرج جاهز للنسخ:")
    
    # مربع كود تفاعلي يحتوي على زرار Copy إلكتروني جاهز
    st.code(final_entry, language=None)
    
    st.success("اضغط على أيقونة النسخ (📋) الموجودة أعلى يمين المربع بالأعلى لنسخ النص مباشرة.")

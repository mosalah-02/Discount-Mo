import streamlit as st
import pypdf
import pandas as pd
import re
import io

st.title("استخراج قيد الخصومات إلى Excel 📊")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
    reader = pypdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # 1. استخراج التواريخ بدقة وضبط الاتجاه (من - إلى)
    dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b', full_text)
    period_str = ""
    if len(dates) >= 2:
        # أخذ تاريخ البداية والنهاية وتنسيقهم
        period_str = f"فترة من {dates[0]} حتى {dates[1]}"
    elif len(dates) == 1:
        period_str = f"بتاريخ {dates[0]}"
        
    # 2. تحديد مكان "البيان التفصيلي" وقراءة الأسطر التابعة له فقط
    lines = full_text.split('\n')
    details_lines = []
    capture = False
    
    for line in lines:
        clean = line.strip()
        # بداية التجميع من عنوان البيان التفصيلي
        if "البيان التفصيلي" in clean or "جرامات × نسبة" in clean:
            capture = True
            continue
        
        if capture:
            # التوقف عند الوصول للجدول التالي مباشرة
            if "توزيع الخصم" in clean or "الإجمالي" in clean or "صفحة" in clean:
                break
            if clean and not clean.startswith("1") and not clean.startswith("2"):
                details_lines.append(clean)
                
    # 3. دمج النصوص لتكوين القيد المطلوب
    combined_details = " و".join(details_lines)
    
    # تحسين تنسيق العلامات لتطابق القيد الحسابي (تنسيق الضرب والخصم)
    combined_details = combined_details.replace(" × ", "*").replace(" جم", "").replace(" ج", "ج")
    
    # القيد النهائي المطلوب
    final_entry = f"{combined_details} {period_str}".strip()
    
    # عرض القيد الناتج وتحميله
    st.success("تم استخراج القيد بنجاح!")
    st.write("**القيد المستخرج:**")
    st.info(final_entry)
    
    # حفظ في إكسيل
    df = pd.DataFrame([{"القيد التفصيلي": final_entry}])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        
    st.download_button(
        label="📥 تحميل ملف Excel",
        data=buffer.getvalue(),
        file_name="discount_entry.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

import streamlit as st
import easyocr
import numpy as np
from PIL import Image

# إعدادات واجهة الموقع
st.set_page_config(page_title="مدقق قيود المحاسبة", layout="centered")

st.title("📂 نظام تدقيق القيود الآلي")
st.write("ارفع صورة القيد للتأكد من أرقام الحسابات والتوجيه المحاسبي")

# الحسابات المعتمدة لديك (التي زودتني بها)
MY_ACCOUNTS = {
    "1010101004": "نقدية المعارض (Cash in Showrooms)",
    "1010203014": "بيوتي سيكرتس (Beauty Secrets)",
    "1010101006": "فروقات النقدية (Cash Discrepancy)",
    "1010101005": "رقابة نقدية المتجر (Store Cash Control)",
    "1010101007": "رقابة الشبكة (POS Networks Control)"
}

# مكان رفع الصورة
uploaded_file = st.file_uploader("اختر صورة القيد (PNG, JPG)...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # عرض الصورة
    image = Image.open(uploaded_file)
    st.image(image, caption='القيد المرفوع', use_column_width=True)
    
    with st.spinner('جاري معالجة البيانات وقراءة الحسابات...'):
        # تحويل الصورة لنظام يفهمه البرنامج
        img_array = np.array(image)
        
        # تشغيل قارئ النصوص (يدعم العربية والإنجليزية)
        reader = easyocr.Reader(['ar', 'en'])
        results = reader.readtext(img_array, detail=0)
        full_text = " ".join(results)

        st.subheader("🔍 نتيجة الفحص:")
        
        found_any = False
        for acc_num, acc_name in MY_ACCOUNTS.items():
            if acc_num in full_text:
                st.success(f"✅ تم العثور على حساب: **{acc_num}** - {acc_name}")
                found_any = True
        
        # تنبيه خاص بحساب الفروقات
        if "1010101006" in full_text:
            st.warning("⚠️ ملاحظة: القيد يحتوي على حساب فروقات (Discrepancy). راجع الوظف المسؤول.")

        if not found_any:
            st.error("❌ لم يتم التعرف على أي من حساباتك المعتمدة في هذه الصورة.")
            
        st.info("نصيحة: تأكد من وضوح الصورة وإضاءتها للحصول على أدق النتائج.")

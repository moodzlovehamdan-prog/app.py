import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import re
import io

# إعدادات واجهة المحاسب الذكي
st.set_page_config(page_title="Dynamics ERP Accountant Bot", layout="wide")

st.title("📑 محاسب داينمك الذكي | Dynamics AI Accountant")
st.write("نظام التدقيق الآلي واستخراج التقارير من صور القيود")

# --- قاعدة بيانات الحسابات المعتمدة ---
ACCOUNTS_MAP = {
    "1010101004": "CASH IN SHOWROOMS",
    "1010203014": "Beauty Secrets",
    "1010101006": "Cash Discrepancy",
    "1010101005": "Store Cash - Control",
    "1010101007": "POS Networks – Control"
}

uploaded_file = st.file_uploader("📸 ارفع صورة القيد من شاشة الداينمك", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='القيد الجاري تحليله', use_container_width=True)
    
    with st.spinner('جاري المسح الشامل للأعمدة والمبالغ...'):
        img_array = np.array(image)
        reader = easyocr.Reader(['ar', 'en'])
        results = reader.readtext(img_array)
        
        # استخراج النصوص والبيانات
        extracted_data = []
        for res in results:
            extracted_data.append(res[1])
        
        full_text = " ".join(extracted_data).upper()

        # --- محرك التحليل المحاسبي ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 تفاصيل القيد المستخرجة")
            
            # قراءة التاريخ ورقم القيد والأبعاد
            date_found = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', full_text)
            voucher_found = re.findall(r'SGTU-\d+', full_text)
            dim_found = re.findall(r'VRM\.UAE\.\d+', full_text)
            
            if date_found: st.write(f"📅 **التاريخ:** {date_found[0]}")
            if voucher_found: st.write(f"🔢 **رقم القيد (Voucher):** {voucher_found[0]}")
            if dim_found: st.write(f"🏢 **الأبعاد (Dimensions):** {', '.join(set(dim_found))}")

        with col2:
            st.subheader("🛠️ الحسابات والعمليات")
            found_accs = [acc for acc in ACCOUNTS_MAP if acc in full_text]
            for acc in found_accs:
                st.success(f"✅ تم رصد حساب: {acc} - {ACCOUNTS_MAP[acc]}")
            
            if "نقص توريد" in full_text or "1010101006" in full_text:
                st.warning("⚠️ تنبيه: تم اكتشاف عجز نقدي (Cash Discrepancy)")

        # --- قسم استخراج ملف Excel ---
        st.subheader("📥 استخراج البيانات إلى Excel")
        
        # تجهيز جدول البيانات
        df_data = {
            "Date": date_found[0] if date_found else "N/A",
            "Voucher": voucher_found[0] if voucher_found else "N/A",
            "Accounts Detected": ", ".join(found_accs),
            "Dimensions": ", ".join(set(dim_found)) if dim_found else "N/A",
            "Description Found": "نقص توريد / CDM / POS" if any(x in full_text for x in ["نقص", "CDM", "POS"]) else "N/A"
        }
        df = pd.DataFrame([df_data])

        # تحويل الجدول لملف Excel في الذاكرة
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit_Report')
        processed_data = output.getvalue()

        st.download_button(
            label="تحميل تقرير التدقيق (Excel)",
            data=processed_data,
            file_name="Dynamics_Audit_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.divider()
st.caption("برنامج مساعد للمحاسب محمد باسم - Senior Inventory Accountant")

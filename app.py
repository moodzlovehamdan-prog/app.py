import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import re
import io

# إعدادات واجهة البرنامج
st.set_page_config(page_title="Dynamics Smart Auditor", layout="wide")

st.title("🤖 محاسب داينمك الذكي | Dynamics AI Auditor")
st.write("نظام فحص القيود الآلي واستخراج تقارير الإكسل")

# --- قاعدة بيانات الحسابات المعتمدة لديك ---
ACCOUNTS_MAP = {
    "1010101004": "CASH IN SHOWROOMS",
    "1010203014": "Beauty Secrets (Transit)",
    "1010101006": "Cash Discrepancy (العجز)",
    "1010101005": "Store Cash - Control",
    "1010101007": "POS Networks – Control"
}

# قائمة الأبعاد المالية (التي ظهرت في صورك)
DIMENSIONS_LIST = ["20723", "20732", "20721"]

uploaded_file = st.file_uploader("📸 ارفع صورة القيد من شاشة الداينمك", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='القيد الجاري فحصه', use_container_width=True)
    
    with st.spinner('جاري المسح الشامل للأعمدة والمبالغ...'):
        img_array = np.array(image)
        # قراءة النصوص بالعربي والإنجليزي
        reader = easyocr.Reader(['ar', 'en'])
        results = reader.readtext(img_array)
        
        # استخراج النصوص والبيانات
        raw_text = [res[1] for res in results]
        full_content = " ".join(raw_text).upper()

        # --- تحليل البيانات المستخرجة ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 تفاصيل القيد المكتشفة")
            
            # استخراج التاريخ ورقم القيد
            date_match = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', full_content)
            voucher_match = re.findall(r'SGTU-\d+', full_content)
            
            if date_match: st.info(f"📅 **التاريخ:** {date_match[0]}")
            if voucher_match: st.info(f"🔢 **رقم القيد:** {voucher_match[0]}")
            
            # استخراج الأبعاد (مثل VRM.UAE.20723)
            found_dims = [d for d in DIMENSIONS_LIST if d in full_content]
            if found_dims:
                st.write(f"🏢 **الأبعاد المالية (Branches):** {', '.join(found_dims)}")

        with col2:
            st.subheader("🛠️ التوجيه المحاسبي")
            found_accs = []
            for acc, name in ACCOUNTS_MAP.items():
                if acc in full_content:
                    st.success(f"✅ تم رصد حساب: {acc} - {name}")
                    found_accs.append(acc)
            
            # منطق "خبير المحاسبة"
            if "1010101006" in found_accs:
                st.warning("⚠️ تنبيه محاسبي: هذا القيد يحتوي على 'تسوية عجز نقدية'.")
            if "CDM" in full_content:
                st.info("💰 نوع العملية: إيداع نقدي (Cash Deposit)")

        # --- قسم استخراج ملف Excel ---
        st.subheader("📥 استخراج البيانات إلى Excel")
        
        # تجهيز جدول البيانات للتقرير
        report_data = {
            "Date": date_match[0] if date_match else "N/A",
            "Voucher No": voucher_match[0] if voucher_match else "N/A",
            "Accounts": ", ".join([f"{a} ({ACCOUNTS_MAP[a]})" for a in found_accs]),
            "Dimensions": ", ".join(found_dims) if found_dims else "Missing",
            "Status": "Verified" if len(found_accs) >= 2 else "Check Required"
        }
        
        df = pd.DataFrame([report_data])

        # تحويل لملف Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit_Report')
        excel_file = output.getvalue()

        st.download_button(
            label="تحميل تقرير التدقيق (Excel)",
            data=excel_file,
            file_name=f"Audit_Report_{voucher_match[0] if voucher_match else 'New'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.divider()
st.caption("برنامج مساعد للمحاسب محمد باسم - Senior Inventory Accountant")

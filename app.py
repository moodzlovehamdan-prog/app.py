import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import re
import io

# إعداد واجهة البرنامج
st.set_page_config(page_title="Dynamics Audit Pro", layout="wide")

st.title("🤖 المحاسب الذكي لتدقيق قيود داينمك")
st.write("ارفع صورة القيد وسأقوم بالتحقق من التاريخ، الحسابات، وتوازن القيد")

# --- قائمة الحسابات المعتمدة وقواعد العمل ---
ACCOUNTS_RULES = {
    "1010101004": "CASH IN SHOWROOMS",
    "1010203014": "Beauty Secrets",
    "1010101006": "Cash Discrepancy",
    "1010101005": "Store Cash - Control",
    "1010101007": "POS Networks – Control"
}

uploaded_file = st.file_uploader("📸 ارفع صورة القيد (Snapshot)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='القيد الجاري فحص صحته', use_container_width=True)
    
    with st.spinner('جاري التدقيق المحاسبي وفحص التواريخ...'):
        img_array = np.array(image)
        reader = easyocr.Reader(['ar', 'en'])
        results = reader.readtext(img_array)
        
        raw_text = [res[1] for res in results]
        full_content = " ".join(raw_text).upper()

        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📌 البيانات المستخرجة")
            
            # 1. فحص التاريخ
            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', full_content)
            current_date = dates[0] if dates else "غير معروف"
            st.write(f"📅 **تاريخ القيد:** {current_date}")
            
            # 2. فحص الأبعاد المالية (Dimension)
            branch_match = re.search(r'207\d{2}', full_content)
            branch_code = branch_match.group() if branch_match else "مفقود"
            st.write(f"🏢 **كود الفرع (Dimension):** {branch_code}")

        with col2:
            st.subheader("⚖️ تحليل صحة القيد")
            
            validation_errors = []
            
            # فحص وجود الحسابات
            found_accs = [acc for acc in ACCOUNTS_RULES if acc in full_content]
            
            # منطق التحقق (Validation Logic)
            if not dates:
                validation_errors.append("❌ خطأ: التاريخ غير واضح أو مفقود.")
            
            if branch_code == "مفقود":
                validation_errors.append("❌ خطأ: لم يتم رصد كود الفرع (Dimension).")
                
            if len(found_accs) < 2:
                validation_errors.append("❌ خطأ: القيد غير متوازن (يجب وجود طرفين على الأقل).")

            # عرض النتيجة النهائية
            if not validation_errors:
                st.success("✅ القيد جاهز للتسجيل: كافة البيانات الأساسية مكتملة.")
            else:
                for error in validation_errors:
                    st.error(error)

        # --- أتمتة الوصف المحاسبي ---
        st.subheader("📝 ملخص الحركة")
        if "1010101006" in found_accs:
            st.warning("⚠️ تنبيه: القيد يحتوي على تسوية عجز (Cash Discrepancy). تأكد من إرفاق الموافقات.")
        elif "1010101007" in found_accs or "1010203014" in found_accs:
            st.info("ℹ️ نوع الحركة: تحويل مبيعات (POS/CDM) إلى حسابات الوساطة.")

        # --- استخراج التقرير ---
        report_data = {
            "تاريخ القيد": current_date,
            "كود الفرع": branch_code,
            "الحسابات المكتشفة": ", ".join(found_accs),
            "حالة القيد": "جاهز" if not validation_errors else "يحتاج مراجعة"
        }
        
        df = pd.DataFrame([report_data])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 تحميل تقرير التدقيق (Excel)",
            data=output.getvalue(),
            file_name=f"Audit_{branch_code}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.divider()
st.caption("برنامج مساعد للمحاسب محمد باسم - تدقيق آلي لقيود Dynamics")

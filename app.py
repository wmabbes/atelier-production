import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ضبط إعدادات الصفحة
st.set_page_config(page_title="تطبيق الورشة - متابعة الباكوات", page_icon="🧵", layout="wide")

# CSS لإضافة إطار (Contour) أنيق لمستطيل الإدخال
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .custom-card {
        background-color: #ffffff;
        border: 2px solid #2563eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        border-radius: 8px;
        height: 3.2em;
        font-weight: bold;
        font-size: 16px;
    }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# الاتصال بقاعدة البيانات SQLite
conn = sqlite3.connect('atelier_production.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجدول
c.execute('''
    CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        ouvriere TEXT,
        modele TEXT,
        couleur_ticket TEXT,
        paquet_num INTEGER,
        quantite INTEGER
    )
''')
conn.commit()

st.title("🧵 نظام ورشة الخياطة - الإدخال الجماعي السريع")

menu = st.sidebar.radio("القائمة الرئيسية", ["تسجيل الباكوات (إدخال سريع)", "جدول إنتاج الورشة", "إحصائيات وحسابات العاملات"])

if menu == "تسجيل الباكوات (إدخال سريع)":
    
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📦 مستطيل إدخال الباكوات الجماعي")
    st.write("أدخل بيانات الموديل وجميع أرقام الباكوات دفعة واحدة بدون تكرار.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 بيانات العمل")
        ouvriere = st.text_input("اسم الطفلة / العاملة", placeholder="مثال: مريم، سارة...")
        modele = st.text_input("اسم الموديل", value="رُبّة", placeholder="مثال: رُبّة، قميص...")
        couleur_ticket = st.selectbox("لون التيكي (Ticket)", ["بيضاء", "حمراء", "صفراء", "زرقاء", "خضراء", "وردية", "أخرى"])

    with col2:
        st.markdown("#### 🔢 أرقام الباكوات المنجزة")
        method = st.radio("طريقة الإدخال:", [
            "كتابة أرقام الباكوات مباشرة (مفصولة بفواصل: 1, 2, 3, 5, 8)",
            "من باكو إلى باكو (نطاق متسلسل)"
        ])
        
        if method == "كتابة أرقام الباكوات مباشرة (مفصولة بفواصل: 1, 2, 3, 5, 8)":
            custom_paquets = st.text_input("اكتب أرقام الباكوات هنا مفصولة بفواصل:", value="1, 2, 3, 5, 8")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                start_p = st.number_input("من باكو رقم:", min_value=1, value=1, step=1)
            with col_b:
                end_p = st.number_input("إلى باكو رقم:", min_value=1, value=5, step=1)

        quantite_par_paquet = st.number_input("عدد القطع في كل باكو:", min_value=1, value=12, step=1)

    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 حفظ جميع الباكوات دفعة واحدة", type="primary", use_container_width=True):
        if not ouvriere or not modele:
            st.error("⚠️ يرجى إدخال اسم العاملة واسم الموديل أولاً!")
        else:
            paquets_list = []
            if method == "كتابة أرقام الباكوات مباشرة (مفصولة بفواصل: 1, 2, 3, 5, 8)":
                try:
                    paquets_list = [int(x.strip()) for x in custom_paquets.split(",") if x.strip().isdigit()]
                except Exception:
                    st.error("⚠️ يرجى كتابة الأرقام مفصولة بفواصل بشكل صحيح (مثال: 1, 2, 3, 5, 8)")
            else:
                if start_p > end_p:
                    st.error("⚠️ يجب أن يكون رقم بداية الباكو أصغر من أو يساوي رقم النهاية!")
                else:
                    paquets_list = list(range(int(start_p), int(end_p) + 1))

            if paquets_list:
                today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for p_num in paquets_list:
                    c.execute('''
                        INSERT INTO production (date, ouvriere, modele, couleur_ticket, paquet_num, quantite)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today_str, ouvriere, modele, couleur_ticket, p_num, quantite_par_paquet))
                
                conn.commit()
                total_pcs = len(paquets_list) * quantite_par_paquet
                st.success(f"✅ تم بنجاح تسجيل {len(paquets_list)} باكوات (الأرقام: {paquets_list}) للطفلة [{ouvriere}] - موديل [{modele}] بتيكي [{couleur_ticket}]! المجموع: {total_pcs} قطعة.")

elif menu == "جدول إنتاج الورشة":
    st.subheader("📋 جميع الباكوات المسجلة في الورشة")
    df = pd.read_sql_query("""
        SELECT 
            id AS 'الرقم', 
            date AS 'التاريخ', 
            ouvriere AS 'العاملة', 
            modele AS 'الموديل', 
            couleur_ticket AS 'لون التيكي', 
            paquet_num AS 'رقم الباكو', 
            quantite AS 'عدد القطع'
        FROM production ORDER BY id DESC
    """, conn)
    
    if not df.empty:
        workers = ["الكل"] + list(df['العاملة'].unique())
        selected_worker = st.selectbox("تصفية حسب العاملة:", workers)
        
        if selected_worker != "الكل":
            st.dataframe(df[df['العاملة'] == selected_worker], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد باكوات مسجلة حتى الآن.")

else:
    st.subheader("📊 إحصائيات إنتاج العاملات")
    df = pd.read_sql_query("SELECT ouvriere, quantite, paquet_num FROM production", conn)
    
    if not df.empty:
        total_paquets = len(df)
        total_pieces = df['quantite'].sum()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("إجمالي الباكوات المنجزة", total_paquets)
        col_m2.metric("إجمالي القطع المنجزة", total_pieces)
        
        st.markdown("---")
        st.markdown("### مجموع القطع والباكوات لكل عاملة / طفلة:")
        
        summary = df.groupby("ouvriere").agg(
            عدد_الباكوات=('paquet_num', 'count'),
            مجموع_القطع=('quantite', 'sum')
        ).reset_index()
        
        summary.columns = ["العاملة", "عدد الباكوات", "مجموع القطع"]
        st.table(summary)
        st.bar_chart(summary.set_index("العاملة")["مجموع القطع"])
    else:
        st.info("لا توجد بيانات مسجلة لعرض الإحصائيات.")

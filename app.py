import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import io

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Naseem's Med App — Pro Suite",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Epic CSS ----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, .stApp { font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto; }
    .bg-glow { background: radial-gradient(1200px 600px at 10% 10%, rgba(60,140,255,0.06), transparent 8%), radial-gradient(1000px 500px at 90% 90%, rgba(58,200,160,0.03), transparent 12%); }
    .topbar { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 16px; border-radius:12px; background:linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border:1px solid rgba(255,255,255,0.04); box-shadow: 0 8px 30px rgba(2,8,23,0.45); }
    .brand { font-weight:800; font-size:20px; color: #DDF6FF }
    .subtitle { color:#9FD6FF; font-size:13px }
    .card { border-radius:12px; padding:14px; background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border:1px solid rgba(127,199,255,0.06); box-shadow: 0 8px 24px rgba(2,8,23,0.45); }
    .metric { font-weight:800; font-size:18px }
    .muted { color:#9FBFD8 }
    .btn-primary { padding:8px 14px; border-radius:10px; background:linear-gradient(90deg,#2CB7FF,#6A78FF); color:white; font-weight:700; }
    .small { font-size:13px; color:#9FBFD8 }
    .danger { color:#FF2E63; font-weight:800 }
    .good { color:#0FC57F; font-weight:800 }
    .kpi { display:flex; gap:10px; }
    .kpi .card { flex:1 }
    .table-wrap { max-height:360px; overflow:auto }
    </style>
    """, unsafe_allow_html=True)

# ---------------- Utilities ----------------

PROFESSIONAL_ADVICE = {
    'Underweight': {'remedy': 'High-calorie nutrient-dense diet + progressive resistance training.', 'physical': '5–6 meals/day, protein shakes, 3×/week strength training.', 'tablet': 'Assess clinically; supplements/prn under MD.'},
    'Normal weight': {'remedy': 'Maintain balanced intake and regular activity.', 'physical': '150 min/wk moderate activity.', 'tablet': 'Routine monitoring.'},
    'Overweight': {'remedy': 'Moderate calorie deficit, whole foods, increase NEAT.', 'physical': '150–300 min/wk + resistance training.', 'tablet': 'Discuss options if lifestyle fails.'},
    'Obese': {'remedy': 'Intensive weight-loss program and specialist referral.', 'physical': 'Structured program under supervision.', 'tablet': 'Consider pharmacotherapy or surgical evaluation.'},
    'Normal BP': {'remedy': 'Maintain low sodium, exercise.', 'physical': 'Daily activity, stress control.', 'tablet': 'No meds.'},
    'Elevated BP': {'remedy': 'Reduce sodium & alcohol; home monitoring.', 'physical': '30 min brisk walk/day.', 'tablet': 'Usually no immediate meds.'},
    'Stage 1 HTN': {'remedy': 'DASH diet + weight loss.', 'physical': '30–45 min most days.', 'tablet': 'May need single agent.'},
    'Stage 2 HTN': {'remedy': 'Urgent medical review and rapid lifestyle change.', 'physical': 'Supervised increase.', 'tablet': 'Often needs medication.'},
    'Normal Sugar': {'remedy': 'Low-GI diet; portion control', 'physical': '150 min/wk activity.', 'tablet': 'No meds.'},
    'Pre-Diabetes': {'remedy': '5–7% weight loss goal; reduce refined carbs', 'physical': '150–300 min/wk', 'tablet': 'Metformin in selected cases.'},
    'Diabetes': {'remedy': 'Carb control, monitoring, preventive care', 'physical': 'Structured exercise + education', 'tablet': 'Individualised therapy.'}
}

RISK_STATUS = {
    'Underweight': ('WARNING','badge-warn'),
    'Normal weight': ('GOOD','badge-good'),
    'Overweight': ('BAD','badge-bad'),
    'Obese': ('CRITICAL','badge-crit'),
    'Normal BP': ('GOOD','badge-good'),
    'Elevated BP': ('WARNING','badge-warn'),
    'Stage 1 HTN': ('BAD','badge-bad'),
    'Stage 2 HTN': ('CRITICAL','badge-crit'),
    'Normal Sugar': ('GOOD','badge-good'),
    'Pre-Diabetes': ('WARNING','badge-warn'),
    'Diabetes': ('CRITICAL','badge-crit')
}

# BMI/bp/sugar helpers

def calculate_bmi(weight_kg, height_cm):
    h_m = height_cm / 100.0
    if h_m <= 0:
        return None, None
    bmi = weight_kg / (h_m * h_m)
    bmi_val = round(bmi, 1)
    if bmi < 18.5:
        cat = 'Underweight'
    elif bmi < 25:
        cat = 'Normal weight'
    elif bmi < 30:
        cat = 'Overweight'
    else:
        cat = 'Obese'
    return bmi_val, cat


def get_bp_category(systolic, diastolic):
    if systolic >= 140 or diastolic >= 90:
        return f"{int(systolic)}/{int(diastolic)} mmHg", 'Stage 2 HTN'
    elif systolic >= 130 or diastolic >= 80:
        return f"{int(systolic)}/{int(diastolic)} mmHg", 'Stage 1 HTN'
    elif 120 <= systolic < 130 and diastolic < 80:
        return f"{int(systolic)}/{int(diastolic)} mmHg", 'Elevated BP'
    else:
        return f"{int(systolic)}/{int(diastolic)} mmHg", 'Normal BP'


def get_sugar_category(fasting_mgdl):
    if fasting_mgdl >= 126:
        return f"{int(fasting_mgdl)} mg/dL", 'Diabetes'
    elif 100 <= fasting_mgdl <= 125:
        return f"{int(fasting_mgdl)} mg/dL", 'Pre-Diabetes'
    else:
        return f"{int(fasting_mgdl)} mg/dL", 'Normal Sugar'


def badge_html(text, cls):
    return f"<span class='{cls}' style='font-size:13px;padding:4px 8px;border-radius:8px'>{text}</span>"

# ---------------- State & persistence helpers ----------------

STORAGE_KEY = 'naseem_med_history'

if STORAGE_KEY not in st.session_state:
    st.session_state[STORAGE_KEY] = pd.DataFrame(columns=['timestamp','name','age','sex','height_cm','weight_kg','bmi','bmi_cat','systolic','diastolic','bp_cat','fasting','sugar_cat','activity'])


def add_record(record: dict):
    df = st.session_state[STORAGE_KEY]
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    st.session_state[STORAGE_KEY] = df


def download_df_as_csv(df: pd.DataFrame, filename='naseem_med_history.csv'):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode('utf-8')

# ---------------- Sidebar navigation ----------------
with st.sidebar:
    st.markdown("<div class='brand'>🩺 Naseem Med — Pro Suite</div><div class='subtitle small'>Advanced clinical UI • Multi-page</div>", unsafe_allow_html=True)
    st.markdown('---')
    page = st.radio('Navigation', ['Dashboard','History','Assessments','Settings'])
    st.markdown('---')
    st.markdown('<div class="small muted">Quick Controls</div>', unsafe_allow_html=True)
    if st.button('➕ New blank record'):
        # clear inputs by rerunning with minimal effect
        for k in ['_tmp_clear']: st.session_state[k] = True
        st.experimental_rerun()
    st.markdown('---')
    st.markdown('<div class="small muted">Data Storage</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader('Upload history CSV (optional)', type=['csv'])
    if uploaded is not None:
        try:
            df_u = pd.read_csv(uploaded)
            st.session_state[STORAGE_KEY] = df_u
            st.success('Uploaded history loaded')
        except Exception as e:
            st.error('Failed to load CSV: '+str(e))

# ---------------- Pages ----------------

# --- DASHBOARD ---
if page == 'Dashboard':
    st.markdown("<div class='topbar bg-glow'><div><div class='brand'>Naseem's Medical — Pro Suite</div><div class='subtitle'>Interactive clinical summary • Advanced visuals</div></div><div class='small muted'>Last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "</div></div>", unsafe_allow_html=True)

    st.markdown('## Enter patient data')
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        name = st.text_input('Patient name', value='Anonymous')
        age = st.number_input('Age', min_value=0, max_value=120, value=25)
        sex = st.selectbox('Sex', ['Male','Female','Other'])
    with c2:
        height = st.number_input('Height (cm)', min_value=50, max_value=230, value=170)
        weight = st.number_input('Weight (kg)', min_value=1, max_value=300, value=70)
    with c3:
        systolic = st.number_input('Systolic (mmHg)', min_value=50, max_value=250, value=120)
        diastolic = st.number_input('Diastolic (mmHg)', min_value=30, max_value=150, value=80)
        fasting = st.number_input('Fasting glucose (mg/dL)', min_value=40, max_value=600, value=90)
        activity = st.selectbox('Activity', ['Sedentary','Light','Moderate','Very Active'])

    st.markdown('---')
    gen_col, spacer = st.columns([1,3])
    with gen_col:
        if st.button('📊 Generate full report'):
            bmi_val, bmi_cat = calculate_bmi(weight, height)
            bp_score, bp_cat = get_bp_category(systolic, diastolic)
            sugar_score, sugar_cat = get_sugar_category(fasting)

            # save record
            rec = {
                'timestamp': datetime.utcnow().isoformat(),
                'name': name, 'age': age, 'sex': sex, 'height_cm': height, 'weight_kg': weight,
                'bmi': bmi_val, 'bmi_cat': bmi_cat, 'systolic': systolic, 'diastolic': diastolic, 'bp_cat': bp_cat,
                'fasting': fasting, 'sugar_cat': sugar_cat, 'activity': activity
            }
            add_record(rec)

            # KPIs
            st.markdown('<div class="kpi">', unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"<div class='card'><div class='muted'>BMI</div><div class='metric'>{bmi_val} <div class='muted' style='font-weight:600'>{bmi_cat}</div></div></div>", unsafe_allow_html=True)
            with k2:
                st.markdown(f"<div class='card'><div class='muted'>Blood Pressure</div><div class='metric'>{bp_score} <div class='muted' style='font-weight:600'>{bp_cat}</div></div></div>", unsafe_allow_html=True)
            with k3:
                st.markdown(f"<div class='card'><div class='muted'>Fasting Glucose</div><div class='metric'>{sugar_score} <div class='muted' style='font-weight:600'>{sugar_cat}</div></div></div>", unsafe_allow_html=True)
            with k4:
                immediate = any([RISK_STATUS[bmi_cat][0] in ('CRITICAL','BAD'), RISK_STATUS[bp_cat][0] in ('CRITICAL','BAD'), RISK_STATUS[sugar_cat][0] in ('CRITICAL','BAD')])
                level = 'ATTENTION' if immediate else 'OK'
                cls = 'danger' if immediate else 'good'
                st.markdown(f"<div class='card'><div class='muted'>Quick Risk</div><div class='metric {cls}' style='font-size:18px'>{level}</div></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('---')
            left, right = st.columns([2,1])
            with left:
                st.markdown(f"<div class='card'><h3>Clinical Summary — {name}</h3><div class='muted'>Age: {age} • Sex: {sex} • Activity: {activity}</div><hr></div>", unsafe_allow_html=True)

                with st.expander('BMI — detailed'):
                    bstatus, bcls = RISK_STATUS[bmi_cat]
                    st.markdown(f"<div class='card'><b>BMI:</b> {bmi_val} — <b>{bmi_cat}</b> &nbsp; {badge_html(bstatus, bcls)}</div>", unsafe_allow_html=True)
                    st.write(PROFESSIONAL_ADVICE[bmi_cat]['remedy'])
                    st.write(PROFESSIONAL_ADVICE[bmi_cat]['physical'])
                    st.write(PROFESSIONAL_ADVICE[bmi_cat]['tablet'])

                with st.expander('Blood Pressure — detailed'):
                    pstatus, pcls = RISK_STATUS[bp_cat]
                    st.markdown(f"<div class='card'><b>BP:</b> {bp_score} — <b>{bp_cat}</b> &nbsp; {badge_html(pstatus, pcls)}</div>", unsafe_allow_html=True)
                    st.write(PROFESSIONAL_ADVICE[bp_cat]['remedy'])
                    st.write(PROFESSIONAL_ADVICE[bp_cat]['physical'])
                    st.write(PROFESSIONAL_ADVICE[bp_cat]['tablet'])

                with st.expander('Glucose — detailed'):
                    sstatus, scls = RISK_STATUS[sugar_cat]
                    st.markdown(f"<div class='card'><b>Fasting:</b> {sugar_score} — <b>{sugar_cat}</b> &nbsp; {badge_html(sstatus, scls)}</div>", unsafe_allow_html=True)
                    st.write(PROFESSIONAL_ADVICE[sugar_cat]['remedy'])
                    st.write(PROFESSIONAL_ADVICE[sugar_cat]['physical'])
                    st.write(PROFESSIONAL_ADVICE[sugar_cat]['tablet'])

            with right:
                # interactive plotly BMI trend using session history
                df = st.session_state[STORAGE_KEY]
                if not df.empty:
                    df_plot = df.copy()
                    df_plot['ts'] = pd.to_datetime(df_plot['timestamp'])
                    df_plot = df_plot.sort_values('ts')
                    fig = px.line(df_plot, x='ts', y='bmi', title='BMI over time', markers=True)
                    fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info('No history yet — results will show here after you generate.')

                st.markdown('<div class="card"><h4>Quick Vitals</h4><div class="muted">Systolic</div><div class="metric">' + str(systolic) + ' mmHg</div><div class="muted">Diastolic</div><div class="metric">' + str(diastolic) + ' mmHg</div></div>', unsafe_allow_html=True)

            # share / export
            st.markdown('---')
            coldl, coldr = st.columns([1,1])
            with coldl:
                csv_bytes = download_df_as_csv(st.session_state[STORAGE_KEY])
                st.download_button('📥 Download history CSV', data=csv_bytes, file_name='naseem_med_history.csv', mime='text/csv')
            with coldr:
                st.button('📋 Copy short summary')

# --- HISTORY ---
elif page == 'History':
    st.markdown('<div class="topbar"><div class="brand">History</div><div class="small muted">Stored readings</div></div>', unsafe_allow_html=True)
    df = st.session_state[STORAGE_KEY]
    if df.empty:
        st.info('No records yet. Generate reports from Dashboard to populate history.')
    else:
        st.markdown('### All records')
        with st.expander('Show table', expanded=True):
            st.dataframe(df.sort_values('timestamp', ascending=False))
        st.markdown('### Analytics')
        st.markdown('Visualize trends in BMI, BP and Glucose')
        cols = st.columns(3)
        df_plot = df.copy()
        df_plot['ts'] = pd.to_datetime(df_plot['timestamp'])
        if not df_plot.empty:
            with cols[0]:
                fig = px.line(df_plot, x='ts', y='bmi', title='BMI trend', markers=True)
                st.plotly_chart(fig, use_container_width=True)
            with cols[1]:
                fig2 = px.line(df_plot, x='ts', y='systolic', title='Systolic trend', markers=True)
                st.plotly_chart(fig2, use_container_width=True)
            with cols[2]:
                fig3 = px.line(df_plot, x='ts', y='fasting', title='Fasting glucose', markers=True)
                st.plotly_chart(fig3, use_container_width=True)

        st.markdown('---')
        if st.button('🗑️ Clear history'):
            st.session_state[STORAGE_KEY] = pd.DataFrame(columns=st.session_state[STORAGE_KEY].columns)
            st.success('History cleared')

# --- ASSESSMENTS ---
elif page == 'Assessments':
    st.markdown('<div class="topbar"><div class="brand">Assessments</div><div class="subtitle">Quick calculators & printable reports</div></div>', unsafe_allow_html=True)
    st.markdown('### Quick risk calculators')
    st.markdown('Use values from last entry or enter new ones')
    last = st.session_state[STORAGE_KEY].tail(1)
    if not last.empty:
        last = last.iloc[0]
        st.write('Using last record for quick assessment: ', last['name'])
        st.write('BMI:', last['bmi'], last['bmi_cat'])
        st.write('BP:', last['systolic'], '/', last['diastolic'], last['bp_cat'])
    else:
        st.info('No previous record. Use Dashboard to add one.')

    st.markdown('---')
    st.markdown('### Generate printable summary (PDF/HTML) — lightweight')
    if st.button('Generate printable HTML summary'):
        # simple HTML export
        dfp = st.session_state[STORAGE_KEY].tail(1)
        if dfp.empty:
            st.warning('No record to export')
        else:
            r = dfp.iloc[0]
            html = f"""
            <html><body><h2>Clinical summary — {r['name']}</h2>
            <p>Age: {r['age']} — BMI: {r['bmi']} ({r['bmi_cat']})</p>
            <p>BP: {r['systolic']}/{r['diastolic']} — {r['bp_cat']}</p>
            <p>Fasting: {r['fasting']} — {r['sugar_cat']}</p>
            <p>Generated: {datetime.utcnow().isoformat()}</p>
            </body></html>
            """
            st.download_button('📄 Download HTML summary', data=html, file_name='summary.html', mime='text/html')

# --- SETTINGS ---
elif page == 'Settings':
    st.markdown('<div class="topbar"><div class="brand">Settings</div><div class="subtitle small">Customize app behaviour</div></div>', unsafe_allow_html=True)
    st.markdown('### Appearance')
    st.write('You can edit CSS in the code to change colors and fonts.')
    st.markdown('---')
    st.markdown('### Developer')
    st.code('pip install streamlit plotly pandas matplotlib')
    st.markdown('---')
    st.markdown('App version: **Pro Suite 1.0**')

# ---------------- Footer ----------------
st.markdown('<hr>')
st.markdown("<div style='display:flex;justify-content:space-between'><div class='small muted'>Built by Naseem — For demo & educational use only</div><div class='small muted'>Not a diagnostic tool</div></div>", unsafe_allow_html=True)

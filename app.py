import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Naseem's Med App ",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CSS / Theme (epic neon glass) ----------------
st.markdown(
    """
    <style>
    /* background gradient + subtle animation */
    @keyframes floatBG { 0% {background-position:0% 50%} 50% {background-position:100% 50%} 100% {background-position:0% 50%} }
    html, body, .stApp {
        height:100%;
        background: linear-gradient(120deg, #071428 0%, #042A3A 35%, #071428 100%);
        background-size: 200% 200%;
        animation: floatBG 20s ease infinite;
        color: #EAF6FF;
        font-family: 'Segoe UI', Roboto, -apple-system, 'Helvetica Neue', Arial;
    }

    /* top hero */
    .hero {
        background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.03));
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 8px 30px rgba(2,8,23,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
        backdrop-filter: blur(6px) saturate(140%);
        margin-bottom: 18px;
        border: 1px solid rgba(255,255,255,0.04);
    }

    .brand { font-size:22px; font-weight:700; letter-spacing:0.4px; }
    .tag { color:#9FD6FF; font-size:13px; }

    /* neon cards */
    .card {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid rgba(127,199,255,0.06);
        box-shadow: 0 6px 18px rgba(2,8,23,0.5);
    }

    .big-metric { font-size:20px; font-weight:800; }
    .muted { color: #9FBFD8; }

    /* badges */
    .badge-good { color: #0FC57F; font-weight:800; padding:4px 8px; border-radius:8px; background: rgba(15,197,127,0.06); }
    .badge-warn { color: #FFB020; font-weight:800; padding:4px 8px; border-radius:8px; background: rgba(255,176,32,0.06); }
    .badge-bad { color: #FF6B6B; font-weight:800; padding:4px 8px; border-radius:8px; background: rgba(255,107,107,0.04); }
    .badge-crit { color: #FF2E63; font-weight:900; padding:4px 8px; border-radius:8px; background: rgba(255,46,99,0.06); }

    /* subtle animated glow for CTA */
    .cta {
        padding:10px 18px; border-radius: 12px; font-weight:700; background: linear-gradient(90deg,#2CB7FF, #6A78FF); color: white; border:none; box-shadow: 0 6px 26px rgba(58,110,255,0.18);
    }

    .footer { font-size:12px; color:#9FBFD8 }

    /* responsive small screens */
    @media (max-width: 600px) {
        .brand { font-size:18px; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- Helper dictionaries (kept concise) ----------------
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

# ---------------- Utility functions ----------------

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

# ---------------- Sidebar: user info & quick actions ----------------
with st.sidebar:
    st.markdown("<div style='text-align:center'><h3 class='brand'>🩺 Razeena's Medical App </h3><div class='tag'>Futuristic clinical assistant</div></div>", unsafe_allow_html=True)
    st.markdown("---")

    name = st.text_input("Patient name", value="-")
    age = st.number_input("Age (years)", min_value=0, max_value=120, value=25)
    sex = st.selectbox("Gender", ['Male','Female','Other'])
    contact = st.text_input("Contact / ID (optional)")

    st.markdown("---")
    st.markdown("<div class='muted'>Quick actions</div>", unsafe_allow_html=True)
    if st.button("📄 Export summary (copy) "):
        st.experimental_set_query_params(last_export=datetime.utcnow().isoformat())
        st.success("Summary state captured — use copy from UI (or implement cookie export).")
    if st.button("🎯 Reset inputs"):
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("<div class='muted footer'>Built for demo • Not a diagnostic tool</div>", unsafe_allow_html=True)

# ---------------- Main UI ----------------

st.markdown("<div class='hero'> <div style='display:flex;align-items:center;justify-content:space-between'> <div><div class='brand'>Naseem's Medical App </div><div class='tag'>Interactive clinical summary • Visual & professional</div></div><div style='text-align:right'><div class='muted'>Logged: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "</div></div></div></div>", unsafe_allow_html=True)

# Input area
st.markdown("## 🔎 Enter clinical values")
col1, col2, col3 = st.columns([1,1,1])
with col1:
    height = st.number_input("Height (cm)", min_value=50, max_value=230, value=170)
    weight = st.number_input("Weight (kg)", min_value=1, max_value=300, value=70)
with col2:
    systolic = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=250, value=120)
    diastolic = st.number_input("Diastolic BP (mmHg)", min_value=30, max_value=150, value=80)
with col3:
    fasting = st.number_input("Fasting Blood Sugar (mg/dL)", min_value=40, max_value=600, value=90)
    activity = st.selectbox("Activity level (typical)", ['Sedentary','Light','Moderate','Very Active'])

st.markdown("---")

# Generate button with animation-like UX
if st.button("📊 Generate Report", key='gen'):
    bmi_val, bmi_cat = calculate_bmi(weight, height)
    bp_score, bp_cat = get_bp_category(systolic, diastolic)
    sugar_score, sugar_cat = get_sugar_category(fasting)

    # Top metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"<div class='card'><div class='muted'>BMI</div><div class='big-metric'>{bmi_val} <span class='muted'>({bmi_cat})</span></div></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='card'><div class='muted'>Blood Pressure</div><div class='big-metric'>{bp_score} <span class='muted'>({bp_cat})</span></div></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='card'><div class='muted'>Fasting Glucose</div><div class='big-metric'>{sugar_score} <span class='muted'>({sugar_cat})</span></div></div>", unsafe_allow_html=True)
    with kpi4:
        risk_level = RISK_STATUS[bmi_cat][0]
        st.markdown(f"<div class='card'><div class='muted'>Overall quick risk</div><div class='big-metric'>{risk_level}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Detailed cards
    left, right = st.columns([2,1])
    with left:
        st.markdown(f"<div class='card'><h3>Clinical Summary — {name}</h3><div class='muted'>Age: {age} • Sex: {sex} • Activity: {activity}</div><hr></div>", unsafe_allow_html=True)

        # BMI advice expander
        with st.expander("🔹 BMI — Detailed advice", expanded=True):
            bstatus, bcls = RISK_STATUS[bmi_cat]
            st.markdown(f"<div class='card'><b>BMI:</b> {bmi_val} — <b>{bmi_cat}</b> &nbsp; {badge_html(bstatus, bcls)}</div>", unsafe_allow_html=True)
            st.markdown("**Lifestyle / Dietary Remedy:**")
            st.write(PROFESSIONAL_ADVICE[bmi_cat]['remedy'])
            st.markdown("**Physical / Behavioural:**")
            st.write(PROFESSIONAL_ADVICE[bmi_cat]['physical'])
            st.markdown("**Medical note:**")
            st.write(PROFESSIONAL_ADVICE[bmi_cat]['tablet'])

        # BP advice expander
        with st.expander("🔹 Blood Pressure — Detailed advice", expanded=False):
            pstatus, pcls = RISK_STATUS[bp_cat]
            st.markdown(f"<div class='card'><b>BP:</b> {bp_score} — <b>{bp_cat}</b> &nbsp; {badge_html(pstatus, pcls)}</div>", unsafe_allow_html=True)
            st.write(PROFESSIONAL_ADVICE[bp_cat]['remedy'])
            st.write(PROFESSIONAL_ADVICE[bp_cat]['physical'])
            st.write(PROFESSIONAL_ADVICE[bp_cat]['tablet'])

        # Sugar advice
        with st.expander("🔹 Glucose — Detailed advice", expanded=False):
            sstatus, scls = RISK_STATUS[sugar_cat]
            st.markdown(f"<div class='card'><b>Fasting:</b> {sugar_score} — <b>{sugar_cat}</b> &nbsp; {badge_html(sstatus, scls)}</div>", unsafe_allow_html=True)
            st.write(PROFESSIONAL_ADVICE[sugar_cat]['remedy'])
            st.write(PROFESSIONAL_ADVICE[sugar_cat]['physical'])
            st.write(PROFESSIONAL_ADVICE[sugar_cat]['tablet'])

        # Actionable steps
        st.markdown("<div class='card'><h4>Actionable Next Steps</h4><ul><li>If any category is <b>CRITICAL / BAD</b>, contact a physician immediately.</li><li>Start lifestyle steps: walk, manage diet, log BP/glucose for 1–2 weeks.</li><li>Share this summary with your clinician.</li></ul></div>", unsafe_allow_html=True)

    with right:
        # Small visual: BMI distribution chart simulation
        st.markdown("<div class='card'><h4>Visuals & Trend</h4>", unsafe_allow_html=True)
        # simulate a small trend using numpy
        days = np.arange(-14,1)
        # create a mock BMI trend moving slightly towards current value
        bmi_trend = np.clip(bmi_val + 0.2*np.sin(days/3) + np.linspace(-0.5,0,days.size), 12, 45)
        fig, ax = plt.subplots(figsize=(4,2.2))
        ax.plot(days, bmi_trend)
        ax.set_title('BMI')
        ax.set_xlabel('days')
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

        # Quick vitals card
        st.markdown(f"<div class='card'><h4>Quick Vitals</h4><div class='muted'>Systolic</div><div class='big-metric'>{systolic} mmHg</div><div class='muted'>Diastolic</div><div class='big-metric'>{diastolic} mmHg</div></div>", unsafe_allow_html=True)

        # Risk summary
        st.markdown("<div class='card'><h4>Risk Summary</h4>", unsafe_allow_html=True)
        for cat in [bmi_cat, bp_cat, sugar_cat]:
            status, cls = RISK_STATUS[cat]
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'><div>{cat}</div><div>{badge_html(status, cls)}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # footer + legal
    st.markdown("---")
    st.markdown("<div style='display:flex;justify-content:space-between;align-items:center'><div class='muted small'>Report generated by <b>Naseem Ahamed</b></div><div class='muted small'>Not a diagnostic tool — consult clinician</div></div>", unsafe_allow_html=True)

    # subtle celebration for good results
    critical_flags = [cat for cat in [bmi_cat, bp_cat, sugar_cat] if RISK_STATUS[cat][0] in ('CRITICAL','BAD')]
    if len(critical_flags) == 0:
        st.success('All primary categories are within GOOD/WARNING ranges. Keep it up!')
    else:
        st.warning('One or more categories require attention: ' + ', '.join(critical_flags))

    # allow user to copy a sharable summary text
    if st.button('📋 Copy simple summary'):
        summary = f"{name} | Age {age} | BMI {bmi_val} ({bmi_cat}) | BP {bp_score} ({bp_cat}) | Fasting {sugar_score} ({sugar_cat})"
        st.write('Copy the text below and share with your clinician:')
        st.code(summary)

# ---------------- If user opens without generating ----------------
else:
    st.info('Enter values and press "Generate Epic Report" to see a professional summary with visuals.')

# ---------------- END ----------------

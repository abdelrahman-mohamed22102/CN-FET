import streamlit as st
from groq import Groq
import json
import re

st.set_page_config(
    page_title="Clinical Notes Extractor",
    page_icon="🏥",
    layout="wide",
)

st.markdown("""
<style>
    .main .block-container { padding: 2rem 3rem; max-width: 100%; }
    .app-header { padding: 1.5rem 0 0.5rem 0; margin-bottom: 0.5rem; }
    .app-header h1 { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; margin: 0; }
    .app-header p { color: #6b7280; font-size: 0.95rem; margin: 0.25rem 0 0 0; }

.stTextArea textarea {
    font-size: 0.95rem; line-height: 1.6;
    border-radius: 10px; border: 1.5px solid #374151;
    padding: 1rem; font-family: 'Georgia', serif;
    background: #1e1e2e;
    color: #e5e7eb;
    caret-color: #e5e7eb;
}
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 2.5rem; font-size: 1rem; font-weight: 600;
        cursor: pointer; width: 100%;
    }
    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #1a1a2e;
        margin: 1.5rem 0 1rem 0; padding-bottom: 0.4rem;
        border-bottom: 2px solid #e5e7eb;
    }
    .feature-card {
        background: white; border-radius: 12px; padding: 1rem 1.2rem;
        border: 1.5px solid #e5e7eb; margin-bottom: 0.75rem;
    }
    .card-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
    .card-value { font-size: 1rem; font-weight: 600; color: #111827; line-height: 1.4; }
    .card-note  { font-size: 0.8rem; color: #9ca3af; margin-top: 0.2rem; }

    .label-blue{color:#3b82f6} .label-pink{color:#ec4899} .label-green{color:#10b981}
    .label-orange{color:#f59e0b} .label-red{color:#ef4444} .label-purple{color:#8b5cf6}
    .label-teal{color:#14b8a6} .label-indigo{color:#6366f1}

    .card-blue{border-left:4px solid #3b82f6;background:#eff6ff}
    .card-pink{border-left:4px solid #ec4899;background:#fdf2f8}
    .card-green{border-left:4px solid #10b981;background:#ecfdf5}
    .card-orange{border-left:4px solid #f59e0b;background:#fffbeb}
    .card-red{border-left:4px solid #ef4444;background:#fef2f2}
    .card-purple{border-left:4px solid #8b5cf6;background:#f5f3ff}
    .card-teal{border-left:4px solid #14b8a6;background:#f0fdfa}
    .card-indigo{border-left:4px solid #6366f1;background:#eef2ff}

    .badge{display:inline-block;padding:0.15rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600}
    .badge-red{background:#fee2e2;color:#991b1b}
    .badge-yellow{background:#fef9c3;color:#854d0e}
    .badge-green{background:#dcfce7;color:#166534}
    .badge-gray{background:#f3f4f6;color:#374151}

    .summary-box{background:#f0f9ff;border:1.5px solid #bae6fd;border-radius:12px;padding:1rem 1.25rem;margin-top:1.5rem;font-size:0.9rem;color:#0c4a6e;line-height:1.7}
    .api-box{background:#f0fdf4;border:1.5px solid #86efac;border-radius:10px;padding:0.9rem 1.1rem;font-size:0.88rem;color:#166534;margin-bottom:1.2rem}
</style>
""", unsafe_allow_html=True)

SAMPLE_NOTES = {
    "Cardiac Case": """Patient: John Miller, 67-year-old male, referred by Dr. Sarah Thompson.
Chief Complaint: Chest pain and shortness of breath on exertion for 3 weeks.
History: Known hypertensive (on Amlodipine 10mg), Type 2 DM (Metformin 1000mg BD), smoker 30 pack-years, quit 5 years ago.
Examination: BP 155/95 mmHg, HR 88 bpm irregular, BMI 31.2. JVP elevated. Bilateral crackles at lung bases.
ECG: Atrial fibrillation with ventricular rate 88 bpm. ST depression V4-V6.
Echo: EF 38%, moderate mitral regurgitation, hypokinesia of lateral wall.
Labs: Troponin I 0.08 ng/mL (elevated), BNP 780 pg/mL, HbA1c 8.9%, eGFR 62 mL/min.
Diagnosis: Acute decompensated heart failure secondary to ischemic cardiomyopathy. NSTEMI with underlying AF.
Plan: Admit CCU. Furosemide 40mg IV, Bisoprolol 2.5mg, Anticoagulation with Rivaroxaban, cardiology consult for angiography.""",

    "Oncology Case": """Name: Fatima Al-Hassan, 54F. Presenting with 3-month history of left breast lump and axillary pain.
PMH: No prior malignancy. Mother had breast cancer at 62. BRCA testing pending.
Social: Non-smoker, occasional alcohol. Post-menopausal since age 50.
O/E: 2.5cm firm irregular mass left upper outer quadrant. 2 palpable left axillary nodes.
Imaging: Mammogram BIRADS-5. MRI shows 2.8cm spiculated mass, suspicious axillary adenopathy.
Biopsy: Invasive ductal carcinoma, Grade 3, ER+/PR+/HER2-, Ki-67 28%.
Staging CT: No distant metastases. Stage IIB (T2 N1 M0).
Plan: MDT review. Neoadjuvant chemo (AC-T), lumpectomy + sentinel node biopsy. Radiation + Tamoxifen.""",

    "Pediatric Case": """Patient: Yusuf Ibrahim, 8-year-old male. 4-day history of high fever, sore throat, difficulty swallowing.
Weight: 26 kg. Immunizations up to date.
HPI: Fever up to 39.8C, odynophagia, muffled voice, neck stiffness, drooling.
Examination: T 39.6C, HR 124, RR 24, SpO2 96%. Bilateral tonsillar enlargement with exudate, uvula deviation right, trismus.
Labs: WBC 18,400 (neutrophils 84%), CRP 187 mg/L.
Imaging: Neck ultrasound: 3.1cm peritonsillar fluid collection right.
Diagnosis: Right peritonsillar abscess with early airway compromise.
Management: ENT consult. IV Amoxicillin-Clavulanate + Dexamethasone 0.15mg/kg. Needle aspiration. Monitor airway.""",
}

SYSTEM_PROMPT = """You are a clinical NLP specialist. Extract structured clinical features from the provided medical note.

Return ONLY a valid JSON object — no explanation, no markdown, no code fences, no backticks.

{
  "patient": {
    "name": "string or null",
    "age": "string or null",
    "gender": "string or null",
    "bmi": "string or null",
    "weight": "string or null"
  },
  "vitals": {
    "blood_pressure": "string or null",
    "heart_rate": "string or null",
    "temperature": "string or null",
    "spo2": "string or null",
    "respiratory_rate": "string or null"
  },
  "diagnoses": ["list of diagnosis strings"],
  "symptoms": ["list of symptom strings"],
  "medications": ["list of medication strings with doses"],
  "allergies": [],
  "lab_results": {"key": "value"},
  "imaging": ["list of imaging findings"],
  "risk_factors": ["list"],
  "plan": ["list of management steps"],
  "severity": "critical | high | moderate | low",
  "specialty": "e.g. Cardiology",
  "summary": "2-3 sentence clinical summary"
}

Use null for missing fields, [] for empty lists. severity: critical=life-threatening, high=serious, moderate=significant, low=routine."""


def extract_features(note_text: str, api_key: str) -> dict:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract clinical features:\n\n{note_text}"}
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


def severity_badge(severity: str) -> str:
    mapping = {
        "critical": ("badge-red",    "🔴 Critical"),
        "high":     ("badge-red",    "🟠 High"),
        "moderate": ("badge-yellow", "🟡 Moderate"),
        "low":      ("badge-green",  "🟢 Low"),
    }
    cls, label = mapping.get((severity or "").lower(), ("badge-gray", severity or "Unknown"))
    return f'<span class="badge {cls}">{label}</span>'


def render_card(label, value, color, note=""):
    if value is None or value == "" or value == [] or value == {}:
        return ""
    if isinstance(value, list):
        display = "<br>".join(f"• {v}" for v in value)
    elif isinstance(value, dict):
        display = "<br>".join(f"<b>{k}:</b> {v}" for k, v in value.items() if v)
    else:
        display = str(value)
    note_html = f'<div class="card-note">{note}</div>' if note else ""
    # ✅ Single-line HTML — prevents Streamlit's markdown parser from
    #    treating the closing </div> on its own line as literal text
    return (
        f'<div class="feature-card card-{color}">'
        f'<div class="card-label label-{color}">{label}</div>'
        f'<div class="card-value">{display}</div>'
        f'{note_html}'
        f'</div>'
    )


def render_results(data: dict):
    p = data.get("patient", {})
    v = data.get("vitals", {})

    st.markdown('<div class="section-title">Patient Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val, color in [
        (c1, "👤 Patient",   p.get("name"),         "blue"),
        (c2, "🎂 Age",       p.get("age"),           "purple"),
        (c3, "⚕ Gender",     p.get("gender"),        "pink"),
        (c4, "🏥 Specialty", data.get("specialty"),  "indigo"),
    ]:
        with col:
            if val:
                st.markdown(render_card(lbl, val, color), unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        sev = data.get("severity", "")
        if sev:
            st.markdown(
                f'<div class="feature-card card-red"><div class="card-label label-red">⚠ Severity</div>'
                f'<div class="card-value">{severity_badge(sev)}</div></div>',
                unsafe_allow_html=True)
    with s2:
        bmi = p.get("bmi") or p.get("weight")
        if bmi:
            st.markdown(render_card("📊 BMI / Weight", bmi, "teal"), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Vital Signs</div>', unsafe_allow_html=True)
    vital_cols = st.columns(5)
    for (lbl, val, color), col in zip([
        ("🩸 Blood Pressure", v.get("blood_pressure"),  "red"),
        ("💓 Heart Rate",     v.get("heart_rate"),       "pink"),
        ("🌡 Temperature",    v.get("temperature"),      "orange"),
        ("💨 SpO₂",           v.get("spo2"),             "blue"),
        ("🫁 Resp. Rate",     v.get("respiratory_rate"), "teal"),
    ], vital_cols):
        with col:
            if val:
                st.markdown(render_card(lbl, val, color), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Clinical Findings</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(render_card("🩺 Diagnoses",    data.get("diagnoses",   []), "red"),    unsafe_allow_html=True)
        st.markdown(render_card("🤒 Symptoms",     data.get("symptoms",    []), "orange"), unsafe_allow_html=True)
    with f2:
        st.markdown(render_card("💊 Medications",  data.get("medications", []), "green"),  unsafe_allow_html=True)
        st.markdown(render_card("⚠ Risk Factors",  data.get("risk_factors",[]), "purple"), unsafe_allow_html=True)
    with f3:
        st.markdown(render_card("🔬 Lab Results",  data.get("lab_results", {}), "blue"),   unsafe_allow_html=True)
        st.markdown(render_card("🖼 Imaging",      data.get("imaging",     []), "teal"),   unsafe_allow_html=True)

    plan = data.get("plan", [])
    if plan:
        st.markdown('<div class="section-title">Management Plan</div>', unsafe_allow_html=True)
        st.markdown(render_card("📋 Plan", plan, "indigo"), unsafe_allow_html=True)

    summary = data.get("summary")
    if summary:
        st.markdown(
            f'<div class="summary-box"><b>Clinical Summary:</b> {summary}</div>',
            unsafe_allow_html=True)


# ── LAYOUT ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>🏥 Clinical Notes Extractor</h1>
    <p>Paste any clinical note — AI extracts structured patient data instantly</p>
</div>
""", unsafe_allow_html=True)

# st.markdown("""
# <div class="api-box">
#     <b>Free API key:</b> Go to 
#     <a href="https://console.groq.com" target="_blank"><b>console.groq.com</b></a> 
#     → Sign up → API Keys → Create Key &nbsp;|&nbsp; No credit card needed &nbsp;|&nbsp; Model: <b>Llama 3.3 70B</b>
# </div>
# """, unsafe_allow_html=True)

# api_key = st.text_input(
#     "Groq API Key",
#     type="password",
#     placeholder="gsk_xxxxxxxxxxxxxxxxxxxx",
#     help="Paste your free Groq API key here"
# )

# st.markdown("---")
api_key = "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"
st.markdown("**Try a sample note:**")
s_cols = st.columns(len(SAMPLE_NOTES))
for i, (label, note_text) in enumerate(SAMPLE_NOTES.items()):
    with s_cols[i]:
        if st.button(f"📋 {label}", use_container_width=True):
            st.session_state["note_input"] = note_text
            st.rerun()

note = st.text_area(
    label="Clinical Note",
    value=st.session_state.get("note_input", ""),
    height=220,
    placeholder="Paste clinical notes here — patient demographics, symptoms, vitals, labs, diagnosis, medications, plan...",
    label_visibility="collapsed",
)

_, btn_col, _ = st.columns([3, 2, 3])
with btn_col:
    submitted = st.button("⚡ Extract Features", use_container_width=True)

if submitted:
    if not api_key.strip():
        st.error("Please enter your Groq API key above.")
    elif not note.strip():
        st.warning("Please paste a clinical note first.")
    else:
        with st.spinner("Analyzing with Llama 3.3 70B..."):
            try:
                data = extract_features(note, api_key.strip())
                st.markdown("---")
                render_results(data)
            except json.JSONDecodeError as e:
                st.error(f"Could not parse model response as JSON: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

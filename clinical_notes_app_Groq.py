import streamlit as st
from groq import Groq
import json
import re
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

st.set_page_config(page_title="Clinical Notes Extractor", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    .main .block-container { padding: 2rem 3rem; max-width: 100%; }
    .app-header { padding: 1.5rem 0 0.5rem 0; margin-bottom: 0.5rem; }
    .app-header h1 { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; margin: 0; }
    .app-header p { color: #6b7280; font-size: 0.95rem; margin: 0.25rem 0 0 0; }
    .stTextArea textarea {
        font-size: 0.95rem; line-height: 1.6; border-radius: 10px;
        border: 1.5px solid #374151; padding: 1rem; font-family: 'Georgia', serif;
        background: #1e1e2e; color: #e5e7eb; caret-color: #e5e7eb;
    }
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 2.5rem; font-size: 1rem; font-weight: 600; width: 100%;
    }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin: 1.5rem 0 1rem 0; padding-bottom: 0.4rem; border-bottom: 2px solid #e5e7eb; }
    .cpg-section-title { font-size: 1.1rem; font-weight: 700; color: #0f4c81; margin: 1.5rem 0 1rem 0; padding-bottom: 0.4rem; border-bottom: 2px solid #bfdbfe; }
    .feature-card { background: white; border-radius: 12px; padding: 1rem 1.2rem; border: 1.5px solid #e5e7eb; margin-bottom: 0.75rem; }
    .card-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
    .card-value { font-size: 1rem; font-weight: 600; color: #111827; line-height: 1.4; }
    .card-note { font-size: 0.8rem; color: #9ca3af; margin-top: 0.2rem; }
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
    .badge-red{background:#fee2e2;color:#991b1b} .badge-yellow{background:#fef9c3;color:#854d0e}
    .badge-green{background:#dcfce7;color:#166534} .badge-gray{background:#f3f4f6;color:#374151}
    .cpg-card { background:#f0f7ff; border:1.5px solid #bfdbfe; border-left:5px solid #2563eb; border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.85rem; }
    .cpg-card-title { font-size:0.95rem; font-weight:700; color:#1e3a5f; margin-bottom:0.35rem; }
    .cpg-card-org { font-size:0.75rem; font-weight:600; color:#2563eb; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.5rem; }
    .cpg-card-link { font-size:0.8rem; margin-top:0.5rem; }
    .cpg-card-link a { color:#1d4ed8; text-decoration:underline; }
    .cpg-source-badge { display:inline-block; font-size:0.7rem; padding:2px 8px; border-radius:999px; background:#dbeafe; color:#1e40af; font-weight:600; margin-right:6px; }
    .cpg-scraped-badge { display:inline-block; font-size:0.7rem; padding:2px 8px; border-radius:999px; background:#dcfce7; color:#166534; font-weight:600; }
    .cpg-llm-badge { display:inline-block; font-size:0.7rem; padding:2px 8px; border-radius:999px; background:#fef9c3; color:#854d0e; font-weight:600; }
    .summary-box { background:#f0f9ff; border:1.5px solid #bae6fd; border-radius:12px; padding:1rem 1.25rem; margin-top:1.5rem; font-size:0.9rem; color:#0c4a6e; line-height:1.7; }
    .agent-status { font-size:0.82rem; color:#6b7280; padding:3px 0; font-style:italic; }
</style>
""", unsafe_allow_html=True)

# ── SAMPLE NOTES ─────────────────────────────────────────────────────────────

SAMPLE_NOTES = {
    "Cardiac Case": """Patient: John Miller, 67-year-old male.
Chief Complaint: Chest pain and shortness of breath on exertion for 3 weeks.
History: Known hypertensive (Amlodipine 10mg), Type 2 DM (Metformin 1000mg BD), smoker 30 pack-years, quit 5 years ago.
Examination: BP 155/95 mmHg, HR 88 bpm irregular, BMI 31.2. JVP elevated. Bilateral crackles at lung bases.
ECG: Atrial fibrillation with ventricular rate 88 bpm. ST depression V4-V6.
Echo: EF 38%, moderate mitral regurgitation, hypokinesia of lateral wall.
Labs: Troponin I 0.08 ng/mL (elevated), BNP 780 pg/mL, HbA1c 8.9%, eGFR 62 mL/min.
Diagnosis: Acute decompensated heart failure secondary to ischemic cardiomyopathy. NSTEMI with underlying AF.
Plan: Admit CCU. Furosemide 40mg IV, Bisoprolol 2.5mg, Rivaroxaban, cardiology consult for angiography.""",

    "Oncology Case": """Name: Fatima Al-Hassan, 54F. 3-month history of left breast lump and axillary pain.
PMH: No prior malignancy. Mother had breast cancer at 62. BRCA testing pending.
O/E: 2.5cm firm irregular mass left upper outer quadrant. 2 palpable left axillary nodes.
Imaging: Mammogram BIRADS-5. MRI: 2.8cm spiculated mass, suspicious axillary adenopathy.
Biopsy: Invasive ductal carcinoma, Grade 3, ER+/PR+/HER2-, Ki-67 28%. Stage IIB (T2 N1 M0).
Plan: MDT review. Neoadjuvant chemo (AC-T), lumpectomy + sentinel node biopsy. Radiation + Tamoxifen.""",

    "Pediatric Case": """Patient: Yusuf Ibrahim, 8-year-old male. 4-day high fever, sore throat, difficulty swallowing.
HPI: Fever 39.8C, odynophagia, muffled voice, neck stiffness, drooling.
Examination: T 39.6C, HR 124, RR 24, SpO2 96%. Bilateral tonsillar enlargement with exudate, uvula deviation right, trismus.
Labs: WBC 18,400 (neutrophils 84%), CRP 187 mg/L.
Imaging: Neck US: 3.1cm peritonsillar fluid collection right.
Diagnosis: Right peritonsillar abscess with early airway compromise.
Management: ENT consult. IV Amoxicillin-Clavulanate + Dexamethasone 0.15mg/kg. Needle aspiration. Monitor airway.""",
}

# ── AGENT 1: CLINICAL FEATURE EXTRACTOR ─────────────────────────────────────

EXTRACTION_PROMPT = """You are a clinical NLP specialist. Extract structured clinical features from the medical note.
Return ONLY valid JSON — no markdown, no explanation, no backticks.

{
  "patient": {"name":null,"age":null,"gender":null,"bmi":null,"weight":null},
  "vitals": {"blood_pressure":null,"heart_rate":null,"temperature":null,"spo2":null,"respiratory_rate":null},
  "diagnoses": [],
  "symptoms": [],
  "medications": [],
  "allergies": [],
  "lab_results": {},
  "imaging": [],
  "risk_factors": [],
  "plan": [],
  "severity": "critical | high | moderate | low",
  "specialty": "e.g. Cardiology",
  "summary": "2-3 sentence summary"
}
Use null for missing, [] for empty lists. severity: critical=life-threatening, high=serious, moderate=significant, low=routine."""


def extract_features(note_text: str, api_key: str) -> dict:
    client = Groq(api_key=api_key)
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract clinical features:\n\n{note_text}"}
        ],
        temperature=0.1, max_tokens=2048,
    )
    raw = r.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw)
    return json.loads(raw)


# ── AGENT 2: WEB SCRAPING TOOLS ──────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def scrape_nccih(query: str) -> dict:
    results = []
    try:
        base = "https://www.nccih.nih.gov"
        # Main CPG page
        r = requests.get(f"{base}/health/providers/clinicalpractice", headers=HEADERS, timeout=10)
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            q_words = set(query.lower().split())
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if len(text) > 15 and (q_words & set(text.lower().split()) or "guideline" in text.lower()):
                    href = a["href"]
                    results.append({"title": text, "url": href if href.startswith("http") else base + href, "source": "NCCIH"})
        # NCCIH search
        r2 = requests.get(f"{base}/search?q={urllib.parse.quote(query + ' guidelines')}", headers=HEADERS, timeout=10)
        if r2.ok:
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for a in soup2.find_all("a", href=True)[:10]:
                text = a.get_text(strip=True)
                if len(text) > 20 and "guideline" in text.lower():
                    href = a["href"]
                    results.append({"title": text, "url": href if href.startswith("http") else base + href, "source": "NCCIH"})
    except Exception:
        pass
    return {"source": "NCCIH", "url_checked": "https://www.nccih.nih.gov/health/providers/clinicalpractice", "results": results[:5], "query": query}


def search_pubmed_guidelines(query: str) -> dict:
    results = []
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": f"{query}[Title] AND guideline[pt]", "retmax": 5, "retmode": "json", "sort": "relevance"},
            headers=HEADERS, timeout=10
        )
        if r.ok:
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if ids:
                sr = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                    headers=HEADERS, timeout=10
                )
                if sr.ok:
                    sdata = sr.json()
                    for uid in ids:
                        doc = sdata.get("result", {}).get(uid, {})
                        title = doc.get("title", "")
                        if title:
                            results.append({
                                "title": title, "journal": doc.get("source", ""),
                                "year": doc.get("pubdate", "")[:4],
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                                "source": "PubMed"
                            })
    except Exception:
        pass
    return {"source": "PubMed", "results": results, "query": query}


def search_who_guidelines(query: str) -> dict:
    results = []
    try:
        url = f"https://www.who.int/search?indexCatalogue=genericsearchindex1&searchQuery={urllib.parse.quote(query + ' clinical guideline')}&wordsMode=0"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True)[:15]:
                text = a.get_text(strip=True)
                href = a["href"]
                if len(text) > 20 and any(k in text.lower() for k in ["guideline", "recommendation", "clinical"]):
                    full_url = href if href.startswith("http") else "https://www.who.int" + href
                    results.append({"title": text[:120], "url": full_url, "source": "WHO"})
    except Exception:
        pass
    return {"source": "WHO", "results": results[:3], "query": query}


def search_ahrq_guidelines(query: str) -> dict:
    results = []
    try:
        url = f"https://www.ahrq.gov/search/index.html?q={urllib.parse.quote(query + ' clinical guideline')}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True)[:15]:
                text = a.get_text(strip=True)
                href = a["href"]
                if len(text) > 20 and any(k in text.lower() for k in ["guideline", "evidence", "clinical", "practice"]):
                    full_url = href if href.startswith("http") else "https://www.ahrq.gov" + href
                    results.append({"title": text[:120], "url": full_url, "source": "AHRQ"})
    except Exception:
        pass
    return {"source": "AHRQ", "results": results[:3], "query": query}


TOOL_FUNCTIONS = {
    "scrape_nccih": scrape_nccih,
    "search_pubmed_guidelines": search_pubmed_guidelines,
    "search_who_guidelines": search_who_guidelines,
    "search_ahrq_guidelines": search_ahrq_guidelines,
}

CPG_TOOLS = [
    {"type": "function", "function": {
        "name": "scrape_nccih",
        "description": "Search NCCIH (National Center for Complementary and Integrative Health) clinical practice guidelines page at https://www.nccih.nih.gov/health/providers/clinicalpractice",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Medical condition or diagnosis"}}, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "search_pubmed_guidelines",
        "description": "Search PubMed for published clinical practice guidelines. Returns peer-reviewed papers with titles, journals, years, and links.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Medical condition e.g. 'atrial fibrillation', 'heart failure'"}}, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "search_who_guidelines",
        "description": "Search WHO (World Health Organization) for global clinical guidelines.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Medical condition to search for WHO guidelines"}}, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "search_ahrq_guidelines",
        "description": "Search AHRQ (Agency for Healthcare Research and Quality) for evidence-based clinical guidelines.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Medical condition or topic"}}, "required": ["query"]}
    }},
]

CPG_AGENT_SYSTEM = """You are a clinical guidelines research agent. Find relevant Clinical Practice Guidelines (CPGs) for a patient's diagnoses.

Strategy:
1. Call search_pubmed_guidelines for the primary diagnosis
2. Call scrape_nccih for the primary diagnosis (NCCIH is a priority source)
3. Call search_who_guidelines for the specialty/main condition
4. Call search_ahrq_guidelines for additional evidence
5. After all tool calls, synthesize into final JSON

Output ONLY this JSON (no markdown, no explanation):
{
  "guidelines": [
    {
      "title": "Full guideline title",
      "organization": "Issuing org (ACC/AHA, WHO, NICE, NCCIH, etc.)",
      "key_recommendations": ["2-3 concise actionable recommendations"],
      "url": "Direct URL to guideline",
      "source_type": "scraped | knowledge",
      "year": "Year or estimated",
      "relevance": "Why this applies to the patient"
    }
  ],
  "search_summary": "One sentence: what was found and from which sources"
}

Rules:
- source_type = "scraped" if found via tool, "knowledge" if from your training
- Always include authoritative URLs (stable official URLs even for knowledge entries)
- Include 3-5 guidelines total
- If tools return empty results, use your medical knowledge with accurate official URLs
- Stable fallback URLs: https://www.nccih.nih.gov/health/providers/clinicalpractice | https://pubmed.ncbi.nlm.nih.gov/ | https://www.acc.org/guidelines | https://www.who.int/publications/who-guidelines | https://www.ahrq.gov/prevention/guidelines"""


def run_cpg_agent(diagnoses: list, specialty: str, api_key: str, status_box) -> dict:
    client = Groq(api_key=api_key)
    diag_str = ", ".join(diagnoses[:4]) if diagnoses else "unspecified"
    messages = [
        {"role": "system", "content": CPG_AGENT_SYSTEM},
        {"role": "user", "content": f"Find CPGs for patient with:\n- Diagnoses: {diag_str}\n- Specialty: {specialty or 'General Medicine'}\n\nSearch all sources then synthesize."}
    ]

    for _ in range(10):
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=CPG_TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=3000,
        )
        msg = resp.choices[0].message

        # Build assistant message dict
        asst_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            asst_msg["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        messages.append(asst_msg)

        # No tool calls → agent finished
        if not msg.tool_calls:
            raw = (msg.content or "").strip()
            raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw)
            # Find JSON object in response
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                raw = match.group(0)
            try:
                return json.loads(raw)
            except Exception:
                break

        # Execute tools
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except Exception:
                fn_args = {}

            status_box.markdown(
                f'<div class="agent-status">🔍 Searching <b>{fn_name.replace("_"," ").title()}</b> → "{fn_args.get("query","")}"</div>',
                unsafe_allow_html=True
            )

            fn = TOOL_FUNCTIONS.get(fn_name)
            result = fn(**fn_args) if fn else {"error": f"Unknown: {fn_name}"}
            time.sleep(0.4)

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    # Fallback synthesis
    status_box.markdown('<div class="agent-status">🤖 Synthesizing results...</div>', unsafe_allow_html=True)
    final = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages + [{"role": "user", "content": "Output ONLY the final JSON with guidelines array. No markdown."}],
        temperature=0.1, max_tokens=2000,
    )
    raw = final.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        return json.loads(raw)
    except Exception:
        return {"guidelines": [], "search_summary": "Could not parse CPG response."}


# ── RENDER HELPERS ────────────────────────────────────────────────────────────

def severity_badge(s):
    m = {"critical":("badge-red","🔴 Critical"),"high":("badge-red","🟠 High"),"moderate":("badge-yellow","🟡 Moderate"),"low":("badge-green","🟢 Low")}
    cls, lbl = m.get((s or "").lower(), ("badge-gray", s or "Unknown"))
    return f'<span class="badge {cls}">{lbl}</span>'


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
    return (f'<div class="feature-card card-{color}">'
            f'<div class="card-label label-{color}">{label}</div>'
            f'<div class="card-value">{display}</div>'
            f'{note_html}</div>')


def render_cpg_section(cpg_data: dict):
    guidelines = cpg_data.get("guidelines", [])
    summary = cpg_data.get("search_summary", "")
    st.markdown('<div class="cpg-section-title">📚 Suggested Clinical Practice Guidelines (CPG)</div>', unsafe_allow_html=True)
    if summary:
        st.markdown(f'<div style="font-size:0.82rem;color:#6b7280;margin-bottom:0.8rem;font-style:italic">Sources checked: NCCIH · PubMed · WHO · AHRQ &nbsp;|&nbsp; {summary}</div>', unsafe_allow_html=True)
    if not guidelines:
        st.info("No guidelines retrieved. Check network access to NCCIH, PubMed, WHO, AHRQ.")
        return

    cols = st.columns(1)
    for g in guidelines:
        title = g.get("title", "Unnamed Guideline")
        org = g.get("organization", "")
        recs = g.get("key_recommendations", [])
        url = g.get("url", "")
        year = g.get("year", "")
        relevance = g.get("relevance", "")
        stype = g.get("source_type", "knowledge")

        src_badge = '<span class="cpg-scraped-badge">✓ Live Retrieved</span>' if stype == "scraped" else '<span class="cpg-llm-badge">✦ AI Knowledge</span>'
        year_html = f'&nbsp;·&nbsp;<span style="font-size:0.75rem;color:#64748b">{year}</span>' if year else ""
        recs_html = ("<ul style='margin:0.4rem 0 0 1rem;padding:0'>" +
                     "".join(f"<li style='font-size:0.85rem;color:#1e40af;margin-bottom:0.25rem'>{r}</li>" for r in recs) +
                     "</ul>") if recs else ""
        rel_html = f'<div style="font-size:0.78rem;color:#64748b;margin-top:0.4rem"><i>Relevance: {relevance}</i></div>' if relevance else ""
        link_html = f'<div class="cpg-card-link">🔗 <a href="{url}" target="_blank">{url[:90]}{"..." if len(url)>90 else ""}</a></div>' if url else ""

        st.markdown(f"""<div class="cpg-card">
            <div class="cpg-card-org"><span class="cpg-source-badge">{org}</span>{src_badge}{year_html}</div>
            <div class="cpg-card-title">{title}</div>
            {recs_html}{rel_html}{link_html}
        </div>""", unsafe_allow_html=True)


def render_results(data: dict):
    p = data.get("patient", {})
    v = data.get("vitals", {})
    st.markdown('<div class="section-title">Patient Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val, color in [(c1,"👤 Patient",p.get("name"),"blue"),(c2,"🎂 Age",p.get("age"),"purple"),(c3,"⚕ Gender",p.get("gender"),"pink"),(c4,"🏥 Specialty",data.get("specialty"),"indigo")]:
        with col:
            if val: st.markdown(render_card(lbl, val, color), unsafe_allow_html=True)
    s1, s2, _, _ = st.columns(4)
    with s1:
        if data.get("severity"):
            st.markdown(f'<div class="feature-card card-red"><div class="card-label label-red">⚠ Severity</div><div class="card-value">{severity_badge(data["severity"])}</div></div>', unsafe_allow_html=True)
    with s2:
        bmi = p.get("bmi") or p.get("weight")
        if bmi: st.markdown(render_card("📊 BMI/Weight", bmi, "teal"), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Vital Signs</div>', unsafe_allow_html=True)
    vcols = st.columns(5)
    for (lbl, val, color), col in zip([("🩸 Blood Pressure",v.get("blood_pressure"),"red"),("💓 Heart Rate",v.get("heart_rate"),"pink"),("🌡 Temperature",v.get("temperature"),"orange"),("💨 SpO₂",v.get("spo2"),"blue"),("🫁 Resp. Rate",v.get("respiratory_rate"),"teal")], vcols):
        with col:
            if val: st.markdown(render_card(lbl, val, color), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Clinical Findings</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(render_card("🩺 Diagnoses", data.get("diagnoses",[]), "red"), unsafe_allow_html=True)
        st.markdown(render_card("🤒 Symptoms", data.get("symptoms",[]), "orange"), unsafe_allow_html=True)
    with f2:
        st.markdown(render_card("💊 Medications", data.get("medications",[]), "green"), unsafe_allow_html=True)
        st.markdown(render_card("⚠ Risk Factors", data.get("risk_factors",[]), "purple"), unsafe_allow_html=True)
    with f3:
        st.markdown(render_card("🔬 Lab Results", data.get("lab_results",{}), "blue"), unsafe_allow_html=True)
        st.markdown(render_card("🖼 Imaging", data.get("imaging",[]), "teal"), unsafe_allow_html=True)

    if data.get("plan"):
        st.markdown('<div class="section-title">Management Plan</div>', unsafe_allow_html=True)
        st.markdown(render_card("📋 Plan", data["plan"], "indigo"), unsafe_allow_html=True)
    if data.get("summary"):
        st.markdown(f'<div class="summary-box"><b>Clinical Summary:</b> {data["summary"]}</div>', unsafe_allow_html=True)


# ── LAYOUT ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>🏥 Clinical Notes Extractor + CPG Agent</h1>
    <p>Multi-agent system · Agent 1 extracts features · Agent 2 searches NCCIH, PubMed, WHO & AHRQ for guidelines</p>
</div>
""", unsafe_allow_html=True)

API_KEY = "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"

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
    submitted = st.button("⚡ Extract + Find Guidelines", use_container_width=True)

if submitted:
    if not note.strip():
        st.warning("Please paste a clinical note first.")
    else:
        st.markdown("---")

        # Agent 1
        with st.spinner("🧠 Agent 1 — Extracting clinical features..."):
            try:
                clinical_data = extract_features(note, API_KEY)
            except Exception as e:
                st.error(f"Feature extraction failed: {e}")
                st.stop()

        # Agent 2
        diagnoses = clinical_data.get("diagnoses", [])
        specialty = clinical_data.get("specialty", "General Medicine")

        with st.container():
            st.markdown("**🔎 Agent 2 — Searching Clinical Practice Guidelines...**")
            status_box = st.empty()
            try:
                cpg_data = run_cpg_agent(diagnoses, specialty, API_KEY, status_box)
                status_box.empty()
            except Exception as e:
                status_box.empty()
                cpg_data = {"guidelines": [], "search_summary": f"CPG search error: {e}"}

        # Render CPG first, then features
        render_cpg_section(cpg_data)
        st.markdown("---")
        render_results(clinical_data)

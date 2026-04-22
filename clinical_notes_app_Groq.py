import streamlit as st
from groq import Groq
import json, re, time, urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Clinical Notes Extractor", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    .main .block-container { padding: 2rem 3rem; max-width: 100%; }
    .app-header h1 { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; margin: 0; }
    .app-header p  { color: #6b7280; font-size: 0.95rem; margin: 0.25rem 0 0 0; }

    .stTextArea textarea {
        font-size: 0.95rem; line-height: 1.6; border-radius: 10px;
        border: 1.5px solid #374151; padding: 1rem;
        font-family: 'Georgia', serif;
        background: #1e1e2e; color: #e5e7eb; caret-color: #e5e7eb;
    }
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 2.5rem; font-size: 1rem; font-weight: 600; width: 100%;
    }

    .section-title {
        font-size: 1.05rem; font-weight: 700; color: #1a1a2e;
        margin: 1.4rem 0 0.9rem; padding-bottom: 0.35rem;
        border-bottom: 2px solid #e5e7eb;
    }
    .cpg-section-title {
        font-size: 1.05rem; font-weight: 700; color: #0f4c81;
        margin: 1.4rem 0 0.9rem; padding-bottom: 0.35rem;
        border-bottom: 2px solid #bfdbfe;
    }

    /* Feature cards */
    .feature-card { background:#fff; border-radius:12px; padding:1rem 1.2rem; border:1.5px solid #e5e7eb; margin-bottom:0.75rem; }
    .card-label { font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-bottom:.3rem; }
    .card-value { font-size:0.97rem; font-weight:600; color:#111827; line-height:1.45; }

    .label-blue{color:#3b82f6}   .card-blue{border-left:4px solid #3b82f6;background:#eff6ff}
    .label-pink{color:#ec4899}   .card-pink{border-left:4px solid #ec4899;background:#fdf2f8}
    .label-green{color:#10b981}  .card-green{border-left:4px solid #10b981;background:#ecfdf5}
    .label-orange{color:#f59e0b} .card-orange{border-left:4px solid #f59e0b;background:#fffbeb}
    .label-red{color:#ef4444}    .card-red{border-left:4px solid #ef4444;background:#fef2f2}
    .label-purple{color:#8b5cf6} .card-purple{border-left:4px solid #8b5cf6;background:#f5f3ff}
    .label-teal{color:#14b8a6}   .card-teal{border-left:4px solid #14b8a6;background:#f0fdfa}
    .label-indigo{color:#6366f1} .card-indigo{border-left:4px solid #6366f1;background:#eef2ff}

    .badge{display:inline-block;padding:.15rem .6rem;border-radius:999px;font-size:.75rem;font-weight:600}
    .badge-red{background:#fee2e2;color:#991b1b}
    .badge-yellow{background:#fef9c3;color:#854d0e}
    .badge-green{background:#dcfce7;color:#166534}
    .badge-gray{background:#f3f4f6;color:#374151}

    /* CPG cards */
    .cpg-card {
        background:#f0f7ff; border:1.5px solid #bfdbfe;
        border-left:5px solid #2563eb; border-radius:12px;
        padding:1rem 1.2rem; margin-bottom:1rem;
    }
    .cpg-org   { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:#2563eb; margin-bottom:.35rem; }
    .cpg-title { font-size:.97rem; font-weight:700; color:#1e3a5f; margin-bottom:.45rem; }
    .cpg-rec   { font-size:.84rem; color:#1e40af; margin:0 0 .5rem .9rem; line-height:1.55; }
    .cpg-rel   { font-size:.77rem; color:#64748b; font-style:italic; margin-top:.35rem; }

    .badge-org      { display:inline-block; padding:2px 9px; border-radius:999px; font-size:.7rem; font-weight:600; background:#dbeafe; color:#1e40af; margin-right:5px; }
    .badge-scraped  { display:inline-block; padding:2px 9px; border-radius:999px; font-size:.7rem; font-weight:600; background:#dcfce7; color:#166534; }
    .badge-ai       { display:inline-block; padding:2px 9px; border-radius:999px; font-size:.7rem; font-weight:600; background:#fef9c3; color:#854d0e; }
    .badge-year     { font-size:.72rem; color:#64748b; margin-left:5px; }

    /* Reference expander inner content */
    .ref-box {
        background:#f8fafc; border:1px solid #cbd5e1;
        border-radius:8px; padding:.85rem 1rem;
        font-size:.82rem; color:#334155; line-height:1.65;
        margin-top:.5rem;
    }
    .ref-label { font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#64748b; margin-bottom:.4rem; }
    .ref-snippet { font-style:italic; color:#475569; border-left:3px solid #94a3b8; padding-left:.7rem; margin:.4rem 0; }
    .ref-link a { color:#2563eb; text-decoration:underline; font-size:.82rem; }

    .summary-box { background:#f0f9ff; border:1.5px solid #bae6fd; border-radius:12px; padding:1rem 1.25rem; margin-top:1.5rem; font-size:.9rem; color:#0c4a6e; line-height:1.7; }
    .agent-log   { font-size:.8rem; color:#6b7280; font-style:italic; padding:2px 0; }
    .pipeline-badge { display:inline-block; font-size:.72rem; font-weight:600; padding:3px 10px; border-radius:6px; margin-right:6px; }
    .pb-done { background:#dcfce7; color:#166534; }
    .pb-run  { background:#fef9c3; color:#854d0e; }
    .pb-wait { background:#f3f4f6; color:#6b7280; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SAMPLES
# ─────────────────────────────────────────────────────────────

SAMPLE_NOTES = {
    "Cardiac": """Patient: John Miller, 67M.
Complaint: Chest pain, SOB on exertion x3 weeks.
Hx: Hypertension (Amlodipine 10mg), T2DM (Metformin 1000mg BD), 30-pack-yr smoker (quit 5yr).
Exam: BP 155/95, HR 88 irregular, BMI 31.2, elevated JVP, bilateral basal crackles.
ECG: AF, ventricular rate 88, ST depression V4-V6.
Echo: EF 38%, moderate MR, lateral wall hypokinesia.
Labs: Troponin I 0.08 ng/mL, BNP 780 pg/mL, HbA1c 8.9%, eGFR 62.
Dx: Acute decompensated HF, ischemic cardiomyopathy, NSTEMI, AF.
Plan: CCU admit, Furosemide 40mg IV, Bisoprolol 2.5mg, Rivaroxaban, angiography.""",

    "Oncology": """Name: Fatima Al-Hassan, 54F.
Hx: Left breast lump x3 months, axillary pain. Mother: breast Ca age 62. BRCA pending.
Exam: 2.5cm spiculated mass LUO quadrant, 2 palpable axillary nodes.
Imaging: BIRADS-5 mammogram, MRI 2.8cm mass + suspicious adenopathy.
Biopsy: IDC Grade 3, ER+/PR+/HER2-, Ki-67 28%. Staging CT: no mets. Stage IIB T2N1M0.
Plan: MDT, AC-T neoadjuvant chemo, lumpectomy + SLNB, radiation, Tamoxifen.""",

    "Pediatric": """Pt: Yusuf Ibrahim, 8M, 26kg.
Hx: Fever 39.8°C, sore throat, odynophagia, muffled voice, drooling x4 days.
Exam: T39.6, HR124, RR24, SpO2 96%. Bilateral tonsillar exudate, uvula deviation right, trismus.
Labs: WBC 18,400 (84% neutrophils), CRP 187 mg/L.
US: 3.1cm peritonsillar collection right.
Dx: Right peritonsillar abscess, early airway compromise.
Plan: ENT consult, IV Amox-Clav + Dexa 0.15mg/kg, needle aspiration, airway monitoring.""",
}

API_KEY = "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"

# ─────────────────────────────────────────────────────────────
# AGENT 1 — Feature Extractor
# ─────────────────────────────────────────────────────────────

A1_SYSTEM = """You are a clinical NLP specialist. Extract structured features from medical notes.
Return ONLY valid JSON — no markdown, no explanation.

Schema:
{
  "patient":  {"name":null,"age":null,"gender":null,"bmi":null,"weight":null},
  "vitals":   {"blood_pressure":null,"heart_rate":null,"temperature":null,"spo2":null,"respiratory_rate":null},
  "diagnoses":      [],
  "symptoms":       [],
  "medications":    [],
  "allergies":      [],
  "lab_results":    {},
  "imaging":        [],
  "risk_factors":   [],
  "plan":           [],
  "severity":  "critical|high|moderate|low",
  "specialty": "e.g. Cardiology",
  "summary":   "2-3 sentence summary"
}
null for missing, [] for empty. severity: critical=life-threatening, high=serious, moderate=significant, low=routine."""


def agent1_extract(note: str) -> dict:
    client = Groq(api_key=API_KEY)
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": A1_SYSTEM},
            {"role": "user",   "content": f"Extract features:\n\n{note}"}
        ],
        temperature=0.05, max_tokens=2048,
    )
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', r.choices[0].message.content.strip())
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────
# AGENT 2 — CPG Research Agent (receives structured features)
# ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ── Scraping tools ──────────────────────────────────────────

def _safe_get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r if r.ok else None
    except Exception:
        return None


def tool_scrape_nccih(query: str) -> dict:
    """Search NCCIH clinical practice guidelines — primary source."""
    results, raw_snippets = [], []
    base = "https://www.nccih.nih.gov"
    cpg_url = f"{base}/health/providers/clinicalpractice"

    r = _safe_get(cpg_url)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        q_words = set(query.lower().split())
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if len(text) > 15 and (q_words & set(text.lower().split()) or "guideline" in text.lower()):
                href = a["href"]
                full = href if href.startswith("http") else base + href
                results.append({"title": text, "url": full})
                raw_snippets.append(f"[NCCIH page] {text} → {full}")

    # Also try NCCIH search
    r2 = _safe_get(f"{base}/search?q={urllib.parse.quote(query + ' guidelines')}")
    if r2:
        soup2 = BeautifulSoup(r2.text, "html.parser")
        for a in soup2.find_all("a", href=True)[:12]:
            text = a.get_text(strip=True)
            if len(text) > 20 and any(k in text.lower() for k in ["guideline", "recommendation", "practice"]):
                href = a["href"]
                full = href if href.startswith("http") else base + href
                results.append({"title": text, "url": full})
                raw_snippets.append(f"[NCCIH search] {text} → {full}")

    return {
        "source": "NCCIH",
        "source_url": cpg_url,
        "results": results[:6],
        "raw_evidence": raw_snippets[:6],
        "query": query,
        "found": len(results)
    }


def tool_pubmed(query: str) -> dict:
    """Search PubMed for published clinical practice guidelines."""
    results, raw_snippets = [], []
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":f"{query}[Title] AND guideline[pt]","retmax":5,"retmode":"json","sort":"relevance"},
            headers=HEADERS, timeout=10
        )
        if r.ok:
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if ids:
                sr = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db":"pubmed","id":",".join(ids),"retmode":"json"},
                    headers=HEADERS, timeout=10
                )
                if sr.ok:
                    data = sr.json()
                    for uid in ids:
                        doc = data.get("result",{}).get(uid,{})
                        title = doc.get("title","")
                        year  = doc.get("pubdate","")[:4]
                        journal = doc.get("source","")
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
                        if title:
                            results.append({"title":title,"year":year,"journal":journal,"url":url,"pmid":uid})
                            raw_snippets.append(f"[PubMed PMID:{uid}] {title} ({journal}, {year}) → {url}")
    except Exception:
        pass
    return {"source":"PubMed","results":results,"raw_evidence":raw_snippets,"query":query,"found":len(results)}


def tool_who(query: str) -> dict:
    """Search WHO guidelines database."""
    results, raw_snippets = [], []
    url = f"https://www.who.int/search?indexCatalogue=genericsearchindex1&searchQuery={urllib.parse.quote(query + ' clinical guideline')}&wordsMode=0"
    r = _safe_get(url)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:20]:
            text = a.get_text(strip=True)
            href = a["href"]
            if len(text) > 25 and any(k in text.lower() for k in ["guideline","recommendation","clinical"]):
                full = href if href.startswith("http") else "https://www.who.int" + href
                results.append({"title": text[:120], "url": full})
                raw_snippets.append(f"[WHO] {text[:100]} → {full}")
    return {"source":"WHO","results":results[:4],"raw_evidence":raw_snippets[:4],"query":query,"found":len(results)}


def tool_ahrq(query: str) -> dict:
    """Search AHRQ evidence-based guidelines."""
    results, raw_snippets = [], []
    url = f"https://www.ahrq.gov/search/index.html?q={urllib.parse.quote(query + ' clinical guideline')}"
    r = _safe_get(url)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:20]:
            text = a.get_text(strip=True)
            href = a["href"]
            if len(text) > 20 and any(k in text.lower() for k in ["guideline","evidence","clinical","practice"]):
                full = href if href.startswith("http") else "https://www.ahrq.gov" + href
                results.append({"title": text[:120], "url": full})
                raw_snippets.append(f"[AHRQ] {text[:100]} → {full}")
    return {"source":"AHRQ","results":results[:4],"raw_evidence":raw_snippets[:4],"query":query,"found":len(results)}


TOOL_FNS = {
    "tool_scrape_nccih": tool_scrape_nccih,
    "tool_pubmed":       tool_pubmed,
    "tool_who":          tool_who,
    "tool_ahrq":         tool_ahrq,
}

CPG_TOOLS = [
    {"type":"function","function":{
        "name":"tool_scrape_nccih",
        "description":"PRIMARY SOURCE: Scrape NCCIH (National Center for Complementary and Integrative Health) clinical practice guidelines from https://www.nccih.nih.gov/health/providers/clinicalpractice. Always call this first.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Primary diagnosis or medical condition"}},"required":["query"]}
    }},
    {"type":"function","function":{
        "name":"tool_pubmed",
        "description":"Search PubMed for peer-reviewed published clinical practice guidelines. Returns titles, journals, years, PMIDs and direct links.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Diagnosis or condition e.g. 'atrial fibrillation' or 'heart failure'"}},"required":["query"]}
    }},
    {"type":"function","function":{
        "name":"tool_who",
        "description":"Search WHO (World Health Organization) global clinical guidelines database.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Medical condition to search WHO guidelines"}},"required":["query"]}
    }},
    {"type":"function","function":{
        "name":"tool_ahrq",
        "description":"Search AHRQ (Agency for Healthcare Research and Quality) for evidence-based guidelines and recommendations.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Medical condition or specialty"}},"required":["query"]}
    }},
]

A2_SYSTEM = """You are a Clinical Practice Guidelines (CPG) research agent.
You receive STRUCTURED clinical features extracted from a patient note — NOT the raw note.
Use these features to search for the most relevant, stable, authoritative CPGs.

PIPELINE:
1. Call tool_scrape_nccih with the PRIMARY diagnosis (NCCIH is the priority source)
2. Call tool_pubmed with the PRIMARY diagnosis
3. Call tool_pubmed with the SECONDARY diagnosis (if present)
4. Call tool_who with the specialty/main condition
5. Call tool_ahrq with the primary diagnosis
6. Synthesize ALL tool results into final JSON

OUTPUT — return ONLY this JSON (no markdown, no backticks, no explanation):
{
  "guidelines": [
    {
      "title":                "Full official guideline title",
      "organization":         "Issuing body (ACC/AHA, WHO, NCCIH, NICE, etc.)",
      "year":                 "Publication year or best estimate",
      "key_recommendations":  ["Concise actionable recommendation 1", "Recommendation 2", "Recommendation 3"],
      "url":                  "Direct stable URL to the guideline",
      "source_type":          "scraped OR knowledge",
      "source_tool":          "tool that returned this (tool_scrape_nccih / tool_pubmed / tool_who / tool_ahrq / knowledge)",
      "raw_evidence":         "Exact snippet or entry returned by the tool that proves this was found",
      "relevance":            "One sentence: why this applies to this patient's features"
    }
  ],
  "sources_checked": ["NCCIH", "PubMed", "WHO", "AHRQ"],
  "search_summary": "One sentence summary of what was found"
}

RULES:
- source_type = "scraped" ONLY if a tool actually returned this entry in raw_evidence
- source_type = "knowledge" if using your medical training (still provide accurate official URL)
- raw_evidence = the exact text snippet from the tool result, or "from medical knowledge" if not scraped
- Always include 3-5 guidelines
- Stable fallback URLs: https://www.nccih.nih.gov/health/providers/clinicalpractice | https://pubmed.ncbi.nlm.nih.gov/ | https://www.acc.org/guidelines | https://www.who.int/publications/who-guidelines"""


def agent2_cpg(features: dict, status_box) -> dict:
    """CPG agent receives structured features from Agent 1."""
    client = Groq(api_key=API_KEY)

    # Build a clean feature summary to pass to Agent 2 (not raw note)
    diagnoses   = features.get("diagnoses", [])
    specialty   = features.get("specialty", "General Medicine")
    age         = features.get("patient", {}).get("age", "unknown")
    gender      = features.get("patient", {}).get("gender", "unknown")
    severity    = features.get("severity", "unknown")
    risk_factors= features.get("risk_factors", [])
    meds        = features.get("medications", [])

    feature_summary = f"""STRUCTURED PATIENT FEATURES (from Agent 1):
- Primary diagnoses:  {', '.join(diagnoses[:4]) if diagnoses else 'unspecified'}
- Specialty:          {specialty}
- Patient:            {age}, {gender}
- Severity:           {severity}
- Risk factors:       {', '.join(risk_factors[:4]) if risk_factors else 'none listed'}
- Current meds:       {', '.join(meds[:4]) if meds else 'none listed'}

Find the most relevant, authoritative CPGs for these diagnoses. Search all 4 sources."""

    messages = [
        {"role": "system",  "content": A2_SYSTEM},
        {"role": "user",    "content": feature_summary},
    ]

    all_raw_evidence = {}  # tool_name → raw results for reference panel

    for _iter in range(12):
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=CPG_TOOLS,
            tool_choice="auto",
            temperature=0.15,
            max_tokens=3500,
        )
        msg = resp.choices[0].message

        asst = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            asst["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        messages.append(asst)

        if not msg.tool_calls:
            raw = (msg.content or "").strip()
            raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw)
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                raw = m.group(0)
            try:
                result = json.loads(raw)
                result["_raw_tool_evidence"] = all_raw_evidence
                return result
            except Exception:
                break

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except Exception:
                fn_args = {}

            query = fn_args.get("query", "")
            status_box.markdown(
                f'<div class="agent-log">🔍 <b>{fn_name}</b> → searching: "<i>{query}</i>"</div>',
                unsafe_allow_html=True
            )

            fn = TOOL_FNS.get(fn_name)
            tool_result = fn(**fn_args) if fn else {"error": f"Unknown tool: {fn_name}"}
            all_raw_evidence[f"{fn_name}:{query}"] = tool_result
            time.sleep(0.3)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result)
            })

    # Fallback synthesis
    status_box.markdown('<div class="agent-log">🤖 Synthesizing all results...</div>', unsafe_allow_html=True)
    final = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages + [{"role":"user","content":"Output ONLY the final JSON. No markdown."}],
        temperature=0.1, max_tokens=2500,
    )
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', final.choices[0].message.content.strip())
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m: raw = m.group(0)
    try:
        result = json.loads(raw)
        result["_raw_tool_evidence"] = all_raw_evidence
        return result
    except Exception:
        return {"guidelines": [], "search_summary": "Parse error.", "_raw_tool_evidence": all_raw_evidence}


# ─────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────

def sev_badge(s):
    m = {"critical":("badge-red","🔴 Critical"),"high":("badge-red","🟠 High"),
         "moderate":("badge-yellow","🟡 Moderate"),"low":("badge-green","🟢 Low")}
    cls, lbl = m.get((s or "").lower(), ("badge-gray", s or "—"))
    return f'<span class="badge {cls}">{lbl}</span>'


def feature_card(label, value, color):
    if not value or value in ([], {}): return ""
    if isinstance(value, list):
        body = "<br>".join(f"• {v}" for v in value)
    elif isinstance(value, dict):
        body = "<br>".join(f"<b>{k}:</b> {v}" for k, v in value.items() if v)
    else:
        body = str(value)
    return (f'<div class="feature-card card-{color}">'
            f'<div class="card-label label-{color}">{label}</div>'
            f'<div class="card-value">{body}</div></div>')


def render_cpg_cards(cpg_data: dict):
    guidelines = cpg_data.get("guidelines", [])
    summary    = cpg_data.get("search_summary", "")
    sources    = cpg_data.get("sources_checked", ["NCCIH","PubMed","WHO","AHRQ"])
    raw_tool   = cpg_data.get("_raw_tool_evidence", {})

    st.markdown('<div class="cpg-section-title">📚 Clinical Practice Guidelines (CPG)</div>', unsafe_allow_html=True)

    # Sources searched bar
    srcs_html = " · ".join(f'<span class="badge-org">{s}</span>' for s in sources)
    st.markdown(f'<div style="font-size:.8rem;color:#6b7280;margin-bottom:.6rem">Sources searched: {srcs_html}</div>', unsafe_allow_html=True)
    if summary:
        st.markdown(f'<div style="font-size:.82rem;color:#475569;font-style:italic;margin-bottom:1rem">{summary}</div>', unsafe_allow_html=True)

    if not guidelines:
        st.info("No guidelines retrieved.")
        return

    for g in guidelines:
        title   = g.get("title","Unnamed Guideline")
        org     = g.get("organization","Unknown")
        year    = g.get("year","")
        recs    = g.get("key_recommendations", [])
        url     = g.get("url","")
        stype   = g.get("source_type","knowledge")
        stool   = g.get("source_tool","")
        raw_ev  = g.get("raw_evidence","")
        rel     = g.get("relevance","")

        src_badge = '<span class="badge-scraped">✓ Live Retrieved</span>' if stype == "scraped" else '<span class="badge-ai">✦ AI Knowledge</span>'
        year_html = f'<span class="badge-year">· {year}</span>' if year else ""
        recs_html = "".join(f'<div class="cpg-rec">▸ {r}</div>' for r in recs)
        rel_html  = f'<div class="cpg-rel">Relevance: {rel}</div>' if rel else ""

        # Assemble the card HTML
        st.markdown(f"""<div class="cpg-card">
            <div class="cpg-org"><span class="badge-org">{org}</span>{src_badge}{year_html}</div>
            <div class="cpg-title">{title}</div>
            {recs_html}
            {rel_html}
        </div>""", unsafe_allow_html=True)

        # ── Reference Data expander ───────────────────────────────────
        with st.expander("📎 Reference Data — Proof of Retrieval", expanded=False):
            col_a, col_b = st.columns([1, 1])

            with col_a:
                st.markdown("**Source details**")
                st.markdown(f"""<div class="ref-box">
                    <div class="ref-label">Source type</div>
                    <div style="margin-bottom:.5rem">{'✅ Live scraped from web' if stype=='scraped' else '🧠 From model medical knowledge'}</div>
                    <div class="ref-label">Tool used</div>
                    <div style="margin-bottom:.5rem"><code>{stool or 'N/A'}</code></div>
                    <div class="ref-label">Organization</div>
                    <div style="margin-bottom:.5rem">{org}</div>
                    <div class="ref-label">Year</div>
                    <div>{year or 'Not specified'}</div>
                </div>""", unsafe_allow_html=True)

            with col_b:
                st.markdown("**Raw retrieved evidence**")
                snippet = raw_ev if raw_ev and raw_ev != "from medical knowledge" else "No direct scrape — synthesized from model's medical training."
                st.markdown(f"""<div class="ref-box">
                    <div class="ref-label">Evidence snippet</div>
                    <div class="ref-snippet">{snippet[:400]}{'...' if len(snippet)>400 else ''}</div>
                </div>""", unsafe_allow_html=True)

            # Full link
            if url:
                st.markdown(f"""<div class="ref-box" style="margin-top:.5rem">
                    <div class="ref-label">Official guideline link</div>
                    <div class="ref-link"><a href="{url}" target="_blank">🔗 {url}</a></div>
                </div>""", unsafe_allow_html=True)

            # Show any raw tool data for this tool key
            matching_keys = [k for k in raw_tool if stool and stool.split(":")[0] in k]
            if matching_keys:
                key = matching_keys[0]
                tool_data = raw_tool[key]
                scraped_results = tool_data.get("results", [])
                if scraped_results:
                    st.markdown("**All entries retrieved from this source:**")
                    for entry in scraped_results[:5]:
                        t = entry.get("title","")
                        u = entry.get("url","")
                        y = entry.get("year","")
                        j = entry.get("journal","")
                        meta = f" · {j}" if j else ""
                        meta += f" · {y}" if y else ""
                        if t:
                            st.markdown(f'<div style="font-size:.8rem;padding:4px 0;border-bottom:1px solid #e2e8f0">📄 <b>{t}</b>{meta}<br><a href="{u}" target="_blank" style="color:#2563eb;font-size:.77rem">{u}</a></div>', unsafe_allow_html=True)


def render_features(data: dict):
    p = data.get("patient", {})
    v = data.get("vitals",  {})

    st.markdown('<div class="section-title">Patient Overview</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,lbl,val,color in [(c1,"👤 Patient",p.get("name"),"blue"),(c2,"🎂 Age",p.get("age"),"purple"),(c3,"⚕ Gender",p.get("gender"),"pink"),(c4,"🏥 Specialty",data.get("specialty"),"indigo")]:
        with col:
            if val: st.markdown(feature_card(lbl,val,color), unsafe_allow_html=True)

    s1,s2,_,_ = st.columns(4)
    with s1:
        if data.get("severity"):
            st.markdown(f'<div class="feature-card card-red"><div class="card-label label-red">⚠ Severity</div><div class="card-value">{sev_badge(data["severity"])}</div></div>', unsafe_allow_html=True)
    with s2:
        bmi = p.get("bmi") or p.get("weight")
        if bmi: st.markdown(feature_card("📊 BMI/Weight",bmi,"teal"), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Vital Signs</div>', unsafe_allow_html=True)
    vcols = st.columns(5)
    for (lbl,val,color),col in zip([("🩸 BP",v.get("blood_pressure"),"red"),("💓 HR",v.get("heart_rate"),"pink"),("🌡 Temp",v.get("temperature"),"orange"),("💨 SpO₂",v.get("spo2"),"blue"),("🫁 RR",v.get("respiratory_rate"),"teal")],vcols):
        with col:
            if val: st.markdown(feature_card(lbl,val,color), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Clinical Findings</div>', unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    with f1:
        st.markdown(feature_card("🩺 Diagnoses",   data.get("diagnoses",[]),   "red"),    unsafe_allow_html=True)
        st.markdown(feature_card("🤒 Symptoms",    data.get("symptoms",[]),    "orange"), unsafe_allow_html=True)
    with f2:
        st.markdown(feature_card("💊 Medications", data.get("medications",[]), "green"),  unsafe_allow_html=True)
        st.markdown(feature_card("⚠ Risk Factors", data.get("risk_factors",[]),"purple"), unsafe_allow_html=True)
    with f3:
        st.markdown(feature_card("🔬 Labs",        data.get("lab_results",{}), "blue"),   unsafe_allow_html=True)
        st.markdown(feature_card("🖼 Imaging",     data.get("imaging",[]),     "teal"),   unsafe_allow_html=True)

    if data.get("plan"):
        st.markdown('<div class="section-title">Management Plan</div>', unsafe_allow_html=True)
        st.markdown(feature_card("📋 Plan", data["plan"], "indigo"), unsafe_allow_html=True)

    if data.get("summary"):
        st.markdown(f'<div class="summary-box"><b>Clinical Summary:</b> {data["summary"]}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
  <h1>🏥 Clinical Notes Extractor + CPG Agent</h1>
  <p>Two-agent pipeline · Agent 1 extracts features · Agent 2 uses those features to search NCCIH · PubMed · WHO · AHRQ</p>
</div>
""", unsafe_allow_html=True)

st.markdown("**Try a sample:**")
sc = st.columns(len(SAMPLE_NOTES))
for i,(label,txt) in enumerate(SAMPLE_NOTES.items()):
    with sc[i]:
        if st.button(f"📋 {label}", use_container_width=True):
            st.session_state["note_input"] = txt
            st.rerun()

note = st.text_area(
    label="Clinical Note", label_visibility="collapsed",
    value=st.session_state.get("note_input",""),
    height=220,
    placeholder="Paste clinical note here — demographics, vitals, labs, diagnosis, medications, plan...",
)

# ── Options row ──────────────────────────────────────────────
opt_col, btn_col_outer = st.columns([3, 2])
with opt_col:
    st.markdown("**Options**")
    enable_cpg = st.checkbox(
        "🔍 Enable CPG Agent (searches NCCIH · PubMed · WHO · AHRQ)",
        value=True,
        help="When enabled, a second agent searches live clinical practice guideline sources after feature extraction."
    )

with btn_col_outer:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    submitted = st.button("⚡ Analyse Note", use_container_width=True)

# ── Pipeline status bar ──────────────────────────────────────
if submitted:
    if not note.strip():
        st.warning("Please paste a clinical note first.")
        st.stop()

    st.markdown("---")

    # Pipeline indicator
    cpg_state = "pb-wait" if not enable_cpg else "pb-wait"
    status_row = st.empty()

    def update_status(a1, a2):
        a2_label = "CPG Agent" if enable_cpg else "CPG Agent (disabled)"
        a2_cls = a2 if enable_cpg else "pb-wait"
        status_row.markdown(
            f'<div style="margin-bottom:.75rem">'
            f'<span class="pipeline-badge {a1}">① Feature Extractor</span>'
            f'<span style="color:#9ca3af;margin-right:6px">→</span>'
            f'<span class="pipeline-badge {a2_cls}">{a2_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    update_status("pb-run", "pb-wait")

    # ── AGENT 1 ─────────────────────────────────────────────
    with st.spinner("🧠 Agent 1 — Extracting clinical features from note..."):
        try:
            features = agent1_extract(note)
        except Exception as e:
            st.error(f"Agent 1 failed: {e}")
            st.stop()

    update_status("pb-done", "pb-run" if enable_cpg else "pb-wait")

    # ── AGENT 2 ─────────────────────────────────────────────
    cpg_data = None
    if enable_cpg:
        st.markdown("**🔎 Agent 2 — Searching Clinical Practice Guidelines...**")
        log_box = st.empty()
        try:
            cpg_data = agent2_cpg(features, log_box)
            log_box.empty()
        except Exception as e:
            log_box.empty()
            cpg_data = {"guidelines":[], "search_summary":f"Error: {e}","_raw_tool_evidence":{}}
        update_status("pb-done","pb-done")
    else:
        update_status("pb-done","pb-wait")

    # ── RENDER: CPG first, then features ────────────────────
    if enable_cpg and cpg_data:
        render_cpg_cards(cpg_data)
        st.markdown("---")

    render_features(features)

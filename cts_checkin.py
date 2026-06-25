import streamlit as st
from streamlit_drawable_canvas import st_canvas
from datetime import datetime
import base64, json, io, os, requests
from pathlib import Path
from PIL import Image
import numpy as np
import time

st.set_page_config(page_title="CTS Patient Check-In", page_icon="🏥", layout="centered")

# ── Load logo ──────────────────────────────────────────────────────────────────
logo_path = Path(__file__).parent / "Horizontal Block.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:56px;">'
else:
    logo_html = '<span style="font-size:16px;font-weight:bold;color:#F47C5A;">Comprehensive Therapy Services</span>'

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* ── Landscape iPad kiosk ── */
    .stApp {{
        background: linear-gradient(145deg, #3a9dbf 0%, #2280a0 100%) !important;
        min-height: 100vh;
    }}
    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="manage-app-button"],
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    .stDeployButton,
    [data-testid="baseButton-headerNoPadding"],
    ._profileContainer_gzau3_53,
    ._profilePreview_gzau3_63,
    .viewerBadge_container__r5tak,
    #stDecoration,
    div[class*="StatusWidget"],
    div[data-testid="stStatusWidget"],
    button[kind="header"],
    .st-emotion-cache-zq5wmm {{ display: none !important; }}

    /* Invisible touch blocker over bottom-right toolbar */
    .cts-toolbar-blocker {{
        position: fixed !important;
        bottom: 0 !important;
        right: 0 !important;
        width: 160px !important;
        height: 80px !important;
        z-index: 999999 !important;
        background: transparent !important;
        pointer-events: all !important;
    }}

    /* Force full landscape width */
    .block-container,
    div[data-testid="stAppViewContainer"] > section > div,
    div[data-testid="block-container"] {{
        max-width: 98vw !important;
        width: 98vw !important;
        padding-left: 2vw !important;
        padding-right: 2vw !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }}

    /* Header bar */
    .cts-header {{
        background: white;
        border-radius: 16px;
        border-top: 5px solid #F47C5A;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}
    .cts-contact {{
        font-size: 12px;
        color: #9aabb8;
        text-align: right;
        line-height: 1.8;
    }}

    /* Progress bar */
    .cts-progress {{
        display: flex;
        gap: 8px;
        margin-bottom: 18px;
    }}
    .cts-bar {{
        flex: 1;
        height: 5px;
        border-radius: 99px;
        background: rgba(255,255,255,0.3);
    }}
    .cts-bar-active {{ background: #F47C5A; }}
    .cts-bar-done   {{ background: #8DC572; }}

    /* Cards */
    .cts-card {{
        background: white;
        border-radius: 24px;
        padding: 20px 32px 18px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        margin-bottom: 10px;
    }}
    .cts-step-badge {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #6BBDD4;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}
    .cts-heading {{
        font-size: 30px;
        font-weight: bold;
        color: #2d3e50;
        margin-bottom: 2px;
    }}
    .cts-subheading {{
        font-size: 15px;
        color: #9aabb8;
        margin-bottom: 14px;
    }}

    /* Welcome card */
    .cts-welcome-card {{
        background: white;
        border-radius: 24px;
        padding: 28px 60px 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        text-align: center;
        margin-bottom: 10px;
        max-width: 780px;
        margin-left: auto;
        margin-right: auto;
    }}
    .cts-welcome-icon  {{ font-size: 56px; margin-bottom: 14px; }}
    .cts-welcome-title {{ font-size: 40px; font-weight: bold; color: #F47C5A; margin-bottom: 16px; }}
    .cts-welcome-text  {{ font-size: 16px; color: #4a6070; line-height: 1.75; margin-bottom: 12px; }}
    .cts-welcome-es    {{ font-size: 15px; color: #8aaabb; line-height: 1.75; font-style: italic; margin-bottom: 32px; }}
    .cts-welcome-divider {{ border: none; border-top: 1px solid #eef2f6; margin: 0 0 28px; }}

    /* Attestation box */
    .cts-attest {{
        background: #fffbf3;
        border: 1.5px solid #f5d89a;
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 13px;
        color: #7a6020;
        line-height: 1.75;
        margin-bottom: 16px;
    }}

    /* Success box */
    .cts-success {{
        background: white;
        border-radius: 24px;
        padding: 28px 60px 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        text-align: center;
        max-width: 780px;
        margin-left: auto;
        margin-right: auto;
    }}

    /* Override Streamlit input sizing for kiosk */
    .stTextInput input {{
        font-size: 24px !important;
        padding: 16px 22px !important;
        border-radius: 12px !important;
        border: 2px solid #c0d0dc !important;
        background: #f7fbfd !important;
        color: #1a2a36 !important;
    }}
    .stTextInput input:focus {{
        border-color: #6BBDD4 !important;
        background: white !important;
        color: #1a2a36 !important;
    }}
    .stTextInput input::placeholder {{
        color: #a0b4c0 !important;
    }}
    .stTextInput label,
    .stTextInput label p,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p {{
        font-size: 17px !important;
        font-weight: 700 !important;
        color: #1a2a36 !important;
        opacity: 1 !important;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 12px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 16px 24px !important;
        border: none !important;
        min-height: 60px !important;
    }}
    .stButton > button[kind="primary"] {{
        background: #F47C5A !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(244,124,90,0.3) !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: #eef4f8 !important;
        color: #6a8a9a !important;
    }}
</style>

<div class="cts-header">
    <div>{logo_html}</div>
    <div class="cts-contact">
        2201 N Central Expwy, Suite 110<br>
        Richardson, TX 75080<br>
        📞 214-265-1819 &nbsp;|&nbsp; 📠 214-373-9530<br>
        info@comptherapy.com
    </div>
</div>
""", unsafe_allow_html=True)

# ── RingCentral config ────────────────────────────────────────────────────────
RC_CLIENT_ID     = "4jCbisbV1mddzJRsMA9XOx"
RC_CLIENT_SECRET = "eQ3QaW05GnccEIG07Ld0caWtzCE9rvSGObkQGV6DGW36"
RC_JWT_TOKEN     = "eyJraWQiOiI4NzYyZjU5OGQwNTk0NGRiODZiZjVjYTk3ODA0NzYwOCIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJhdWQiOiJodHRwczovL3BsYXRmb3JtLnJpbmdjZW50cmFsLmNvbS9yZXN0YXBpL29hdXRoL3Rva2VuIiwic3ViIjoiMTUxMzIwMDM0IiwiaXNzIjoiaHR0cHM6Ly9wbGF0Zm9ybS5yaW5nY2VudHJhbC5jb20iLCJleHAiOjM5MjUxMzYyNzMsImlhdCI6MTc3NzY1MjYyNiwianRpIjoidFdQX19KVFRUOE80Ml8wTkNpdXM0dyJ9.Ew3kNZvr1STczQTF59Nz_HzUv-rm0qynDbUx8kksZ5cnSVrEWQ6RkLNMMpGwHmbjEQkjDmNYWBs91thWMlxHpDsBNt0YBAh5SranJBdOuG9CC_7kHFp9maz6inDWls-Fd4AQaaOYM8EcogAU6IXE3DmApNTezhes0ZEG_xAcQf9DNt_WAFAkxOPsvFTmCcHuvoi4_aC-SAnGioXOgXW95upitjO_QAM-fskzDsEFDgnD9LKhvWCYQFfxKOjJBUeaUK1JxWlywLS08lxc37tDIMcYM7_A8eL7XrRKpk0gG7TFsD8EfrsR7nQvBJEex1H0TCDCO9qIXSWctOzcWHCkvA"
RC_FROM_NUMBER   = "+12142651819"

def get_rc_token():
    """Get RingCentral access token via JWT."""
    import base64 as _b64
    auth = _b64.b64encode(f"{RC_CLIENT_ID}:{RC_CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        "https://platform.ringcentral.com/restapi/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Authorization": f"Basic {auth}"},
        data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
              "assertion": RC_JWT_TOKEN},
        timeout=10
    )
    if resp.ok:
        return resp.json().get("access_token")
    return None

def send_rc_sms(token, to_number, message):
    """Send SMS via RingCentral."""
    # Convert float to int first to strip the .0 (CSV numbers read as float)
    try:
        to_number = int(float(str(to_number)))
    except:
        pass
    digits = "".join(c for c in str(to_number) if c.isdigit())
    # If 11 digits starting with 1 (e.g. 12142651819), strip the leading 1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    resp = requests.post(
        "https://platform.ringcentral.com/restapi/v1.0/account/~/extension/~/sms",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
        json={"from": {"phoneNumber": RC_FROM_NUMBER},
              "to": [{"phoneNumber": f"+1{digits}"}],
              "text": message},
        timeout=10
    )
    return resp.ok

# ── Dropbox config ─────────────────────────────────────────────────────────────

def save_pdf_to_dropbox(pdf_bytes, filename):
    try:
        import dropbox as _dbx
        dbx = _dbx.Dropbox(
            oauth2_refresh_token=st.secrets["DROPBOX_REFRESH_TOKEN"],
            app_key=st.secrets["DROPBOX_APP_KEY"],
            app_secret=st.secrets["DROPBOX_APP_SECRET"]
        )
        today = datetime.now().strftime("%Y-%m-%d")
        path = f"/Apps/CTS Schedule Sync/Check-In Records/{today}/{filename}"
        dbx.files_upload(pdf_bytes, path, mode=_dbx.files.WriteMode.overwrite)
        log_path = f"/Apps/CTS Schedule Sync/Check-In Records/{today}/daily_log.csv"
        log_line = f'{datetime.now().strftime("%H:%M:%S")},{filename}\n'
        try:
            _, res = dbx.files_download(log_path)
            existing = res.content.decode("utf-8")
        except:
            existing = "Check-In Time,Patient File\n"
        updated = (existing + log_line).encode("utf-8")
        dbx.files_upload(updated, log_path, mode=_dbx.files.WriteMode.overwrite)
        return True, None
    except Exception as e:
        return False, str(e)

def build_pdf(first, last, dob, parent, sig_image, checkin_time):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle('header', fontSize=16, textColor=colors.HexColor('#2F5496'), spaceAfter=4)
    sub_style    = ParagraphStyle('sub',    fontSize=10, textColor=colors.grey, spaceAfter=12)
    story.append(Paragraph("Comprehensive Therapy Services", header_style))
    story.append(Paragraph("2201 N Central Expwy, Suite 110 · Richardson, TX 75080 · 214-265-1819", sub_style))
    story.append(Paragraph(f"<b>Patient Check-In Record</b> &nbsp;&nbsp; {checkin_time}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    data = [
        ["Patient First Name / Nombre:", first,  "Patient Last Name / Apellido:", last],
        ["Date of Birth / Fecha de Nacimiento:", dob, "Parent/Guardian / Padre o Tutor:", parent],
    ]
    t = Table(data, colWidths=[2.1*inch, 1.6*inch, 2.1*inch, 1.6*inch])
    t.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f0f4f8'), colors.white]),
        ('GRID',      (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING',   (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15*inch))

    attest_en = ("By signing below, I confirm that my child is present today for their "
                 "scheduled therapy appointment at Comprehensive Therapy Services.")
    attest_es = ("Al firmar a continuacion, confirmo que mi hijo/a esta presente hoy para su "
                 "cita de terapia programada en Comprehensive Therapy Services.")
    box_style = ParagraphStyle('box', fontSize=9, leftIndent=8, rightIndent=8,
                                borderPadding=8, backColor=colors.HexColor('#fff8e1'),
                                borderColor=colors.HexColor('#f9a825'), borderWidth=1,
                                borderRadius=4, spaceAfter=10)
    story.append(Paragraph(f"{attest_en}<br/><br/><i>{attest_es}</i>", box_style))

    story.append(Paragraph("<b>Parent/Guardian Signature / Firma del Padre o Tutor:</b>", styles['Normal']))
    story.append(Spacer(1, 0.05*inch))
    if sig_image is not None:
        img_buf = io.BytesIO()
        sig_pil = Image.fromarray(sig_image.astype('uint8'), 'RGBA')
        background = Image.new('RGBA', sig_pil.size, (255, 255, 255, 255))
        background.paste(sig_pil, mask=sig_pil.split()[3])
        background = background.convert('RGB')
        background.save(img_buf, format='PNG')
        img_buf.seek(0)
        sig_rl = RLImage(img_buf, width=3.5*inch, height=1.0*inch)
        story.append(sig_rl)
    else:
        story.append(Paragraph("<i>No signature captured</i>",
                                ParagraphStyle('ns', fontSize=9, textColor=colors.grey)))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"Signed at: {checkin_time}",
                            ParagraphStyle('ts', fontSize=8, textColor=colors.grey)))
    doc.build(story)
    return buf.getvalue()



# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("step", "welcome"), ("submitted", False), ("form_key", 0), ("submitting", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

def reset():
    st.session_state.step = "welcome"
    st.session_state.submitted = False
    st.session_state.submitting = False
    st.session_state.form_key += 1
    for k in ["saved_first", "saved_last", "saved_parent", "saved_sig"]:
        st.session_state.pop(k, None)
    st.rerun()

# ── Progress bar renderer ──────────────────────────────────────────────────────
def render_progress(active_step):
    """active_step: 1, 2, or 3"""
    bars = []
    for i in range(1, 4):
        if i < active_step:
            bars.append('<div class="cts-bar cts-bar-done"></div>')
        elif i == active_step:
            bars.append('<div class="cts-bar cts-bar-active"></div>')
        else:
            bars.append('<div class="cts-bar"></div>')
    st.markdown(f'<div class="cts-progress">{"".join(bars)}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS SUBMISSION (triggered after button lock to prevent double-submit)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.submitting and not st.session_state.submitted:
    first  = st.session_state.get("saved_first", "").strip()
    last   = st.session_state.get("saved_last", "").strip()
    parent = st.session_state.get("saved_parent", "").strip()

    checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{last}_{first}_{datetime.now().strftime('%H%M%S')}.pdf"

    # Restore signature from session state
    sig_raw = st.session_state.get("saved_sig", None)
    sig_image = None
    if sig_raw is not None:
        import numpy as np
        sig_image = np.array(sig_raw)

    with st.spinner("Saving your check-in... / Guardando su registro..."):
        pdf_bytes = build_pdf(first, last, "", parent, sig_image, checkin_time)
        save_pdf_to_dropbox(pdf_bytes, filename)

        # ── Send SMS via RingCentral — read schedule from Dropbox ──
        try:
            import dropbox as _dbx
            import csv, io as _io
            dbx = _dbx.Dropbox(
                oauth2_refresh_token=st.secrets["DROPBOX_REFRESH_TOKEN"],
                app_key=st.secrets["DROPBOX_APP_KEY"],
                app_secret=st.secrets["DROPBOX_APP_SECRET"]
            )
            _, res = dbx.files_download("/Apps/CTS Schedule Sync/daily_schedule.csv")
            csv_text = res.content.decode("utf-8")
            reader = list(csv.DictReader(_io.StringIO(csv_text)))

            # Fuzzy match patient name
            def _normalize(s):
                return s.lower().replace(" ", "").replace("-", "")

            def _levenshtein(a, b):
                m, n = len(a), len(b)
                dp = list(range(n + 1))
                for i in range(1, m + 1):
                    prev, dp[0] = dp[0], i
                    for j in range(1, n + 1):
                        temp = dp[j]
                        dp[j] = prev if a[i-1] == b[j-1] else 1 + min(prev, dp[j], dp[j-1])
                        prev = temp
                return dp[n]

            def _score(csv_name, f, l):
                # Normalize everything
                typed_full = _normalize(f + l)
                typed_first = _normalize(f)
                typed_last  = _normalize(l)
                norm        = _normalize(csv_name)
                if not norm: return 0

                # Full name similarity
                dist_full = _levenshtein(norm, typed_full)
                full_score = 1 - dist_full / max(len(norm), len(typed_full), 1)

                # First name similarity (compare first word of CSV name)
                parts  = csv_name.replace("-", " ").split()
                cfirst = _normalize(parts[0]) if parts else ""
                dist_f = _levenshtein(cfirst, typed_first)
                first_score = 1 - dist_f / max(len(cfirst), len(typed_first), 1)

                # Last name: check ALL words in CSV name against typed last name
                # This handles double last names (e.g. "Lara Fuentes" — parent types "Lara")
                best_last = 0
                for word in parts[1:]:  # skip first name
                    w = _normalize(word)
                    if not w: continue
                    d = _levenshtein(w, typed_last)
                    s = 1 - d / max(len(w), len(typed_last), 1)
                    if s > best_last:
                        best_last = s

                # Also check if typed last name is contained within the full normalized name
                if typed_last and typed_last in norm:
                    best_last = max(best_last, 0.95)

                # Weighted score: last name match counts most
                return (best_last * 0.55) + (first_score * 0.25) + (full_score * 0.20)

            best_score, best_row = 0, None
            for row in reader:
                s = _score(row.get("Patient Name", ""), first, last)
                if s > best_score:
                    best_score, best_row = s, row

            if best_row and best_score >= 0.65:
                token = get_rc_token()
                if token:
                    for i in range(1, 4):
                        phone   = best_row.get(f"Phone{i}",   "").strip()
                        message = best_row.get(f"Message{i}", "").strip()
                        if phone and message:
                            send_rc_sms(token, phone, message)
        except Exception:
            pass  # Silent fail — check-in completes even if SMS fails

    st.session_state.submitting = False
    st.session_state.submitted = True
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SUCCESS SCREEN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.submitted:
    st.markdown("""
    <div class="cts-success">
        <div style="font-size:64px;margin-bottom:12px;">✅</div>
        <h2 style="color:#8DC572;font-size:30px;margin-bottom:8px;">Check-In Complete!</h2>
        <p style="font-size:16px;color:#555;margin-bottom:4px;">Please have a seat — your therapist will be right with you.</p>
        <hr style="border:none;border-top:1px solid #d4edd0;margin:20px 0;">
        <h2 style="color:#8DC572;font-size:26px;margin-bottom:8px;">¡Registro Completado!</h2>
        <p style="font-size:16px;color:#555;">Por favor tome asiento — su terapeuta estará con usted pronto.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Next Patient / Siguiente Paciente →", use_container_width=True, type="primary"):
        reset()

    time.sleep(10)
    reset()

# ══════════════════════════════════════════════════════════════════════════════
# WELCOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "welcome":
    st.markdown("""
    <div class="cts-welcome-card">
        <div class="cts-welcome-icon">👋</div>
        <div class="cts-welcome-title">Welcome!</div>
        <div class="cts-welcome-text">
            Please complete all fields below and sign at the bottom to complete your check-in.
        </div>
        <hr class="cts-welcome-divider">
        <div class="cts-welcome-es">
            ¡Bienvenido! Por favor complete todos los campos a continuación y firme al final para completar su registro.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Tap to Begin →", use_container_width=True, type="primary"):
        st.session_state.step = "step1"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Patient Name
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "step1":
    render_progress(1)
    st.markdown("""
    <div class="cts-card">
        <div class="cts-step-badge">Step 1 of 3</div>
        <div class="cts-heading">What's your child's name?</div>
        <div class="cts-subheading">¿Cuál es el nombre de su hijo/a?</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        first = st.text_input("First Name / Nombre *", key=f"first_{st.session_state.form_key}")
    with col2:
        last = st.text_input("Last Name / Apellido *", key=f"last_{st.session_state.form_key}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "welcome"
            st.rerun()
    with col_next:
        if st.button("Next →", use_container_width=True, type="primary"):
            if not first.strip() or not last.strip():
                st.error("Please enter both first and last name.")
            else:
                st.session_state["saved_first"] = first.strip()
                st.session_state["saved_last"] = last.strip()
                st.session_state.step = "step2"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Parent Name
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "step2":
    render_progress(2)
    st.markdown("""
    <div class="cts-card">
        <div class="cts-step-badge">Step 2 of 3</div>
        <div class="cts-heading">Your name?</div>
        <div class="cts-subheading">Nombre del padre, madre o tutor</div>
    </div>
    """, unsafe_allow_html=True)

    parent = st.text_input("Parent/Guardian Name / Nombre del Padre o Tutor *",
                            key=f"parent_{st.session_state.form_key}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "step1"
            st.rerun()
    with col_next:
        if st.button("Next →", use_container_width=True, type="primary"):
            if not parent.strip():
                st.error("Please enter your name.")
            else:
                st.session_state["saved_parent"] = parent.strip()
                st.session_state.step = "step3"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Signature only (no keyboard fields — solves iPad keyboard issue)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "step3":
    render_progress(3)
    st.markdown("""
    <div class="cts-card">
        <div class="cts-step-badge">Step 3 of 3 — Last step!</div>
        <div class="cts-heading">Please sign below</div>
        <div class="cts-subheading">Por favor firme a continuación</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#e8f6fb;border-radius:10px;padding:12px 16px;margin-bottom:16px;
                font-size:14px;color:#2d7a96;display:flex;align-items:center;gap:10px;">
        ☝️ &nbsp;Your keyboard has been dismissed — just sign in the box below and tap Submit!<br>
        <em style="color:#5a9ab0;">¡Su teclado ha sido ocultado — solo firme abajo y toque Enviar!</em>
    </div>
    <div class="cts-attest">
        <strong style="color:#c48a10;display:block;margin-bottom:8px;">Attestation / Declaración</strong>
        By signing below, I confirm that my child is present today for their scheduled therapy
        appointment at Comprehensive Therapy Services.<br><br>
        <em>Al firmar a continuación, confirmo que mi hijo/a está presente hoy para su cita de
        terapia programada en Comprehensive Therapy Services.</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Sign below / Firme abajo:**")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=2,
        stroke_color="#1a237e",
        background_color="#ffffff",
        height=200,
        width=820,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.form_key}",
    )
    st.caption("Use your finger on iPad or mouse on desktop to sign above.")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_submit = st.columns([1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "step2"
            st.rerun()
    with col_submit:
        # Show disabled spinner if already submitting to prevent double-tap
        if st.session_state.submitting:
            st.button("⏳ Saving... / Guardando...", use_container_width=True,
                      type="primary", disabled=True)
        elif st.button("✅ Submit Check-In / Enviar Registro", use_container_width=True,
                       type="primary", key="submit_checkin_btn"):
            first  = st.session_state.get("saved_first", "").strip()
            last   = st.session_state.get("saved_last", "").strip()
            parent = st.session_state.get("saved_parent", "").strip()

            errors = []
            if not first:  errors.append("First Name (go back to Step 1)")
            if not last:   errors.append("Last Name (go back to Step 1)")
            if not parent: errors.append("Parent Name (go back to Step 2)")

            if errors:
                st.error(f"Please fill in: {', '.join(errors)}")
            else:
                # Save signature to session state before rerun
                sig_image = None
                if canvas_result.image_data is not None:
                    arr = canvas_result.image_data
                    if arr[:,:,3].max() > 0:
                        sig_image = arr.tolist()  # convert for session state storage
                st.session_state["saved_sig"] = sig_image
                # Lock the button immediately to prevent double-submit
                st.session_state.submitting = True
                st.rerun()

        # ── Instant client-side lock: disables the button the moment it's tapped,
        # before Streamlit even processes the click. This stops rapid double-taps
        # that can sneak through during the brief window before rerun completes.
        st.markdown("""
        <script>
        (function() {
            function lockSubmitButton() {
                const buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    const txt = btn.innerText || "";
                    if (txt.includes("Submit Check-In") && !btn.dataset.lockAttached) {
                        btn.dataset.lockAttached = "true";
                        btn.addEventListener('pointerdown', function() {
                            // Visually + functionally disable on the very first touch event
                            btn.disabled = true;
                            btn.style.opacity = "0.6";
                            btn.style.pointerEvents = "none";
                        }, {capture: true});
                    }
                });
            }
            lockSubmitButton();
            setInterval(lockSubmitButton, 500);
        })();
        </script>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("CTS Patient Check-In · Comprehensive Therapy Services · comptherapy.com")

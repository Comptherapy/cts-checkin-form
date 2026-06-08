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
    /* Full-page blue gradient background */
    .stApp {{
        background: linear-gradient(145deg, #3a9dbf 0%, #2280a0 100%) !important;
        min-height: 100vh;
    }}
    /* Hide streamlit chrome */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 620px !important;
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
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}
    .cts-contact {{
        font-size: 11px;
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
        padding: 32px 28px 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        margin-bottom: 8px;
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
        font-size: 26px;
        font-weight: bold;
        color: #2d3e50;
        margin-bottom: 4px;
    }}
    .cts-subheading {{
        font-size: 13px;
        color: #9aabb8;
        margin-bottom: 24px;
    }}

    /* Welcome card */
    .cts-welcome-card {{
        background: white;
        border-radius: 24px;
        padding: 40px 32px 36px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        text-align: center;
        margin-bottom: 8px;
    }}
    .cts-welcome-icon  {{ font-size: 56px; margin-bottom: 14px; }}
    .cts-welcome-title {{ font-size: 34px; font-weight: bold; color: #F47C5A; margin-bottom: 16px; }}
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
        padding: 40px 28px 36px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        text-align: center;
    }}

    /* Override Streamlit input sizing for kiosk */
    .stTextInput input {{
        font-size: 20px !important;
        padding: 14px 18px !important;
        border-radius: 12px !important;
        border: 2px solid #e0eaf0 !important;
        background: #f7fbfd !important;
    }}
    .stTextInput input:focus {{
        border-color: #6BBDD4 !important;
        background: white !important;
    }}
    .stTextInput label {{
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #5a6a7a !important;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 12px !important;
        font-size: 17px !important;
        font-weight: bold !important;
        padding: 14px 20px !important;
        border: none !important;
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

# ── Zapier & Dropbox config ────────────────────────────────────────────────────
ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/27775252/4btlt88/"

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

def fire_zapier(first, last):
    try:
        payload = json.dumps({"IntakeId": f"CTS-{first}-{last}-{datetime.now().strftime('%H%M%S')}",
                               "Type": "CheckIn",
                               "ClientName": f"{first} {last}"})
        requests.post(ZAPIER_WEBHOOK, data=payload,
                      headers={"Content-Type": "application/json"}, timeout=5)
    except:
        pass

# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("step", "welcome"), ("submitted", False), ("form_key", 0)]:
    if key not in st.session_state:
        st.session_state[key] = default

def reset():
    st.session_state.step = "welcome"
    st.session_state.submitted = False
    st.session_state.form_key += 1
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
# SUCCESS SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.submitted:
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
                st.session_state[f"first_{st.session_state.form_key}"] = first
                st.session_state[f"last_{st.session_state.form_key}"] = last
                st.session_state.step = "step2"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Date of Birth
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "step2":
    render_progress(2)
    st.markdown("""
    <div class="cts-card">
        <div class="cts-step-badge">Step 2 of 3</div>
        <div class="cts-heading">Date of birth?</div>
        <div class="cts-subheading">¿Fecha de nacimiento de su hijo/a?</div>
    </div>
    """, unsafe_allow_html=True)

    # Auto-format DOB via JS component
    st.components.v1.html("""
    <style>
      #dob-input {
        width: 100%;
        font-size: 24px;
        padding: 16px 20px;
        border: 2px solid #e0eaf0;
        border-radius: 12px;
        background: #f7fbfd;
        color: #2d3e50;
        outline: none;
        box-sizing: border-box;
        font-family: Arial, sans-serif;
      }
      #dob-input:focus { border-color: #6BBDD4; background: white; }
      label.dob-label {
        font-size: 13px; font-weight: 700; color: #5a6a7a;
        display: block; margin-bottom: 8px; font-family: Arial, sans-serif;
      }
    </style>
    <label class="dob-label">Date of Birth / Fecha de Nacimiento * (MM/DD/YYYY)</label>
    <input id="dob-input" type="text" maxlength="10" placeholder="MM/DD/YYYY" autocomplete="off">
    <script>
      const inp = document.getElementById('dob-input');
      inp.addEventListener('input', function() {
        let v = this.value.replace(/\\D/g, '').substring(0, 8);
        if (v.length >= 5)      v = v.substring(0,2) + '/' + v.substring(2,4) + '/' + v.substring(4);
        else if (v.length >= 3) v = v.substring(0,2) + '/' + v.substring(2);
        this.value = v;
        window.parent.postMessage({type:'streamlit:setComponentValue', value: v}, '*');
      });
    </script>
    """, height=100)

    dob = st.text_input("Date of Birth (hidden sync)", key=f"dob_{st.session_state.form_key}",
                         label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "step1"
            st.rerun()
    with col_next:
        if st.button("Next →", use_container_width=True, type="primary"):
            if not dob.strip():
                st.error("Please enter date of birth.")
            else:
                st.session_state.step = "step3"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Parent Name + Signature
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "step3":
    render_progress(3)
    st.markdown("""
    <div class="cts-card">
        <div class="cts-step-badge">Step 3 of 3</div>
        <div class="cts-heading">Parent or guardian</div>
        <div class="cts-subheading">Nombre del padre, madre o tutor</div>
    </div>
    """, unsafe_allow_html=True)

    parent = st.text_input("Parent/Guardian Name / Nombre del Padre o Tutor *",
                            key=f"parent_{st.session_state.form_key}")

    st.markdown("""
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
        height=160,
        width=560,
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
        if st.button("✅ Submit Check-In / Enviar Registro", use_container_width=True, type="primary"):
            # Pull saved values from state
            first  = st.session_state.get(f"first_{st.session_state.form_key}", "").strip()
            last   = st.session_state.get(f"last_{st.session_state.form_key}", "").strip()
            dob    = st.session_state.get(f"dob_{st.session_state.form_key}", "").strip()

            errors = []
            if not parent.strip(): errors.append("Parent/Guardian Name")
            if not first:          errors.append("First Name (go back to Step 1)")
            if not last:           errors.append("Last Name (go back to Step 1)")
            if not dob:            errors.append("Date of Birth (go back to Step 2)")

            if errors:
                st.error(f"Please fill in: {', '.join(errors)}")
            else:
                sig_image = None
                if canvas_result.image_data is not None:
                    arr = canvas_result.image_data
                    if arr[:,:,3].max() > 0:
                        sig_image = arr

                checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = f"{last}_{first}_{datetime.now().strftime('%H%M%S')}.pdf"

                with st.spinner("Saving your check-in..."):
                    pdf_bytes = build_pdf(first, last, dob, parent.strip(), sig_image, checkin_time)
                    save_pdf_to_dropbox(pdf_bytes, filename)
                    fire_zapier(first, last)

                st.session_state.submitted = True
                st.rerun()

st.markdown("---")
st.caption("CTS Patient Check-In · Comprehensive Therapy Services · comptherapy.com")

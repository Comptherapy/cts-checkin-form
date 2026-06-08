import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import base64, json, io, os, requests
from pathlib import Path

st.set_page_config(page_title="CTS Patient Check-In", page_icon="🏥", layout="centered")

# ── Load logo ──────────────────────────────────────────────────────────────────
logo_path = Path(__file__).parent / "Horizontal Block.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:70px;">'
else:
    logo_html = '<span style="font-size:24px;font-weight:bold;color:#2F5496;">Comprehensive Therapy Services</span>'

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    body {{ font-family: Arial, sans-serif; background: #f0f4f8; }}
    .header {{
        background: #2F5496;
        padding: 16px 24px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }}
    .header-right {{ color: white; text-align: right; font-size: 13px; line-height: 1.6; }}
    .attest-box {{
        background: #fff8e1;
        border-left: 4px solid #f9a825;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 16px 0;
        font-size: 14px;
    }}
    .success-box {{
        background: #e8f5e9;
        border: 2px solid #43a047;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
    }}
</style>
<div class="header">
    <div>{logo_html}</div>
    <div class="header-right">
        2201 N Central Expwy, Suite 110<br>
        Richardson, TX 75080<br>
        📞 214-265-1819 &nbsp;|&nbsp; 📠 214-373-9530<br>
        info@comptherapy.com
    </div>
</div>
""", unsafe_allow_html=True)

# ── Signature pad component ────────────────────────────────────────────────────
SIGNATURE_HTML = """
<div style="font-family:Arial,sans-serif;">
  <canvas id="sigPad" width="520" height="160"
    style="border:2px solid #ccc;border-radius:6px;background:#fff;cursor:crosshair;display:block;"></canvas>
  <div style="margin-top:8px;display:flex;gap:12px;">
    <button onclick="clearSig()"
      style="padding:6px 18px;border:1px solid #aaa;border-radius:4px;cursor:pointer;background:#f5f5f5;">
      Clear / Limpiar
    </button>
    <span id="sigStatus" style="color:#888;font-size:13px;line-height:2.2;">Sign above / Firme arriba</span>
  </div>
  <input type="hidden" id="sigData" value="">
</div>
<script>
const canvas = document.getElementById('sigPad');
const ctx = canvas.getContext('2d');
let drawing = false, hasSig = false;
ctx.strokeStyle = '#1a237e';
ctx.lineWidth = 2.5;
ctx.lineCap = 'round';

function getPos(e) {
  const r = canvas.getBoundingClientRect();
  if (e.touches) return {x: e.touches[0].clientX - r.left, y: e.touches[0].clientY - r.top};
  return {x: e.clientX - r.left, y: e.clientY - r.top};
}
canvas.addEventListener('mousedown',  e => { drawing=true; ctx.beginPath(); const p=getPos(e); ctx.moveTo(p.x,p.y); });
canvas.addEventListener('mousemove',  e => { if(!drawing) return; const p=getPos(e); ctx.lineTo(p.x,p.y); ctx.stroke(); hasSig=true; });
canvas.addEventListener('mouseup',    () => { drawing=false; saveData(); });
canvas.addEventListener('touchstart', e => { e.preventDefault(); drawing=true; ctx.beginPath(); const p=getPos(e); ctx.moveTo(p.x,p.y); }, {passive:false});
canvas.addEventListener('touchmove',  e => { e.preventDefault(); if(!drawing) return; const p=getPos(e); ctx.lineTo(p.x,p.y); ctx.stroke(); hasSig=true; }, {passive:false});
canvas.addEventListener('touchend',   () => { drawing=false; saveData(); });

function saveData() {
  if (!hasSig) return;
  document.getElementById('sigData').value = canvas.toDataURL('image/png');
  document.getElementById('sigStatus').textContent = '✅ Signature captured';
  document.getElementById('sigStatus').style.color = '#2e7d32';
}
function clearSig() {
  ctx.clearRect(0,0,canvas.width,canvas.height);
  hasSig = false;
  document.getElementById('sigData').value = '';
  document.getElementById('sigStatus').textContent = 'Sign above / Firme arriba';
  document.getElementById('sigStatus').style.color = '#888';
}
function getSigData() {
  return document.getElementById('sigData').value;
}
</script>
"""

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

        # Also append to daily log CSV
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

def build_pdf(first, last, dob, parent, sig_b64, checkin_time):
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

    # Header
    header_style = ParagraphStyle('header', fontSize=16, textColor=colors.HexColor('#2F5496'), spaceAfter=4)
    sub_style    = ParagraphStyle('sub',    fontSize=10, textColor=colors.grey, spaceAfter=12)
    story.append(Paragraph("Comprehensive Therapy Services", header_style))
    story.append(Paragraph("2201 N Central Expwy, Suite 110 · Richardson, TX 75080 · 214-265-1819", sub_style))
    story.append(Paragraph(f"<b>Patient Check-In Record</b> &nbsp;&nbsp; {checkin_time}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    # Patient info table
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

    # Attestation
    attest_en = ("By signing below, I confirm that my child is present today for their "
                 "scheduled therapy appointment at Comprehensive Therapy Services.")
    attest_es = ("Al firmar a continuación, confirmo que mi hijo/a está presente hoy para su "
                 "cita de terapia programada en Comprehensive Therapy Services.")
    box_style = ParagraphStyle('box', fontSize=9, leftIndent=8, rightIndent=8,
                                borderPadding=8, backColor=colors.HexColor('#fff8e1'),
                                borderColor=colors.HexColor('#f9a825'), borderWidth=1,
                                borderRadius=4, spaceAfter=10)
    story.append(Paragraph(f"{attest_en}<br/><br/><i>{attest_es}</i>", box_style))

    # Signature
    if sig_b64 and sig_b64.startswith("data:image"):
        img_data = base64.b64decode(sig_b64.split(",")[1])
        img_buf  = io.BytesIO(img_data)
        sig_img  = RLImage(img_buf, width=3.5*inch, height=1.1*inch)
        story.append(Paragraph("<b>Parent/Guardian Signature / Firma del Padre o Tutor:</b>", styles['Normal']))
        story.append(Spacer(1, 0.05*inch))
        story.append(sig_img)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"Signed at: {checkin_time}", ParagraphStyle('ts', fontSize=8, textColor=colors.grey)))

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

# ── State ──────────────────────────────────────────────────────────────────────
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ── Success screen ─────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown("""
    <div class="success-box">
        <div style="font-size:52px;">✅</div>
        <h2 style="color:#2e7d32;margin:10px 0 6px;">Check-In Complete!</h2>
        <p style="font-size:16px;color:#555;">Please have a seat — your therapist will be right with you.</p>
        <hr style="margin:16px 0;border-color:#c8e6c9;">
        <h2 style="color:#2e7d32;margin:6px 0;">¡Registro Completado!</h2>
        <p style="font-size:16px;color:#555;">Por favor tome asiento — su terapeuta estará con usted pronto.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Next Patient / Siguiente Paciente →", use_container_width=True):
        st.session_state.submitted = False
        st.rerun()
    import time; time.sleep(10)
    st.session_state.submitted = False
    st.rerun()

# ── Form ───────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="background:#e3f2fd;border-left:4px solid #1976d2;padding:12px 16px;border-radius:6px;margin-bottom:16px;font-size:14px;">
        <b>Welcome! Please complete all fields below and sign at the bottom to complete your check-in.</b><br>
        <i>¡Bienvenido! Por favor complete todos los campos a continuación y firme al final para completar su registro.</i>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        first = st.text_input("First Name / Nombre *")
    with col2:
        last  = st.text_input("Last Name / Apellido *")

    col3, col4 = st.columns(2)
    with col3:
        dob    = st.text_input("Date of Birth / Fecha de Nacimiento * (MM/DD/YYYY)")
    with col4:
        parent = st.text_input("Parent/Guardian Name / Nombre del Padre o Tutor *")

    st.markdown("""
    <div class="attest-box">
        <b>e-Signature / Firma Electrónica</b><br><br>
        "By signing below, I confirm that my child is present today for their scheduled therapy appointment at Comprehensive Therapy Services."<br><br>
        <i>"Al firmar a continuación, confirmo que mi hijo/a está presente hoy para su cita de terapia programada en Comprehensive Therapy Services."</i>
    </div>
    """, unsafe_allow_html=True)

    # Signature pad
    components.html(SIGNATURE_HTML, height=220)

    sig_input = st.text_input("Signature data (auto-filled)", key="sig_capture",
                               label_visibility="collapsed",
                               placeholder="Signature will appear here after signing above")

    st.caption("👆 Draw your signature in the box above, then paste the signature data if needed. "
               "On iPad, use your finger to sign.")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✅  Submit Check-In / Enviar Registro", use_container_width=True, type="primary"):
        errors = []
        if not first.strip():  errors.append("First Name / Nombre")
        if not last.strip():   errors.append("Last Name / Apellido")
        if not dob.strip():    errors.append("Date of Birth / Fecha de Nacimiento")
        if not parent.strip(): errors.append("Parent/Guardian Name / Padre o Tutor")

        if errors:
            st.error(f"Please fill in: {', '.join(errors)}")
        else:
            checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = f"{last.strip()}_{first.strip()}_{datetime.now().strftime('%H%M%S')}.pdf"

            with st.spinner("Saving your check-in..."):
                pdf_bytes = build_pdf(first.strip(), last.strip(), dob.strip(),
                                      parent.strip(), sig_input.strip(), checkin_time)
                ok, err = save_pdf_to_dropbox(pdf_bytes, filename)
                fire_zapier(first.strip(), last.strip())

            if ok:
                st.session_state.submitted = True
                st.rerun()
            else:
                st.warning(f"Check-in recorded but could not save to Dropbox: {err}")
                st.session_state.submitted = True
                st.rerun()

st.markdown("---")
st.caption("CTS Patient Check-In · Comprehensive Therapy Services · comptherapy.com")

import base64
from datetime import datetime
import io
import json
from zoneinfo import ZoneInfo
import anthropic
import openpyxl
from openpyxl.styles import Alignment
import streamlit as st

# Titel der Anwendung
st.title("🦷 Dental-Rechnungs-Generator")

# Session State initialisieren
if "reset_trigger" not in st.session_state:
  st.session_state.reset_trigger = 0
if "success_generated" not in st.session_state:
  st.session_state.success_generated = False

# 1. Manuelle Eingabe der Rechnungsnummer (z.B. 191)
st.subheader("1. Rechnungsnummer eingeben")
eingabe_nr = st.text_input(
    "Rechnungsnummer (nur die Nummer, z. B. 191):",
    placeholder="191",
    key=f"eingabe_{st.session_state.reset_trigger}",
)

# 2. Laborauftrag fotografieren / hochladen
st.subheader("2. Laborauftrag fotografieren / hochladen")
uploaded_file = st.file_uploader(
    "Auftragszettel als Bild hochladen",
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.reset_trigger}",
)

if uploaded_file is not None:
  st.image(
      uploaded_file, caption="Aufgenommener Zettel", use_column_width=True
  )

  if st.button("🚀 Rechnung automatisch befüllen"):
    with st.spinner(
        "Claude liest den Zettel aus und befüllt deine Vorlage..."
    ):
      try:
        # Bild in Base64 umwandeln
        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Anthropic Client initialisieren
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

        # Präziser Prompt für Claude zur Extraktion
        prompt_text = """Analysiere diesen zahnärztlichen Laborauftrag absolut exakt. 
WICHTIG für die Auftragsnummer: Lese die Nummer Zeichen für Zeichen direkt vom Bild ab. Erfinde keine Ziffern, füge keine zusätzlichen Zahlen ein und korrigiere nichts eigenmächtig. 

Antworte ausschließlich im folgenden JSON-Format (kein Markdown drumherum, nur das reine JSON):
{
  "patientenname": "...",
  "auftragsnummer": "..."
}"""

        message = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ],
        )

        # Antwort sicher extrahieren
        result_text = ""
        for block in message.content:
          if hasattr(block, "text"):
            result_text += block.text

        # JSON parsen
        json_start = result_text.find("{")
        json_end = result_text.rfind("}") + 1
        json_data = json.loads(result_text[json_start:json_end])

        patientenname = json_data.get("patientenname", "Unbekannt")
        auftragsnummer = json_data.get("auftragsnummer", "Unbekannt")

        # Rechnungsnummer zusammenbauen (z. B. 26.191 aus Eingabe 191)
        sauber_nr = eingabe_nr.strip()
        rechnungsnummer_voll = f"26.{sauber_nr}" if sauber_nr else "26.000"

        # Feste Excel-Vorlage aus dem Repository laden
        wb = openpyxl.load_workbook("Vorlage.xlsx")
        ws = wb.active  # Nimmt das Tabellenblatt

        # Zellen exakt nach Vorgabe belegen:
        deutsches_datum = (
            datetime.now(ZoneInfo("Europe/Berlin"))
            .date()
            .strftime("%d.%m.%Y")
        )
        ws["G9"] = deutsches_datum
        ws["G9"].alignment = Alignment(
            horizontal="right"
        )  # Datum rechtsbündig

        ws["G11"] = rechnungsnummer_voll  # Rechnungsnummer in G11
        ws["G12"]  = patientenname  # Patientenname in G12
        ws["G16"] = auftragsnummer  # Auftragsnummer in G16

        # In den Arbeitsspeicher speichern
        output = io.BytesIO()
        wb.save(output)
        excel_data = output.getvalue()

        # In Session State sichern
        st.session_state.excel_data = excel_data
        st.session_state.filename = f"{rechnungsnummer_voll}_Rechnung.xlsx"
        st.session_state.success_generated = True

      except Exception as e:
        st.error(f"Fehler bei der Verarbeitung: {e}")

# Wenn die Rechnung erfolgreich generiert wurde, zeigen wir Download-Link & Reset-Button an
if st.session_state.success_generated:
  st.success("Rechnung wurde erfolgreich befüllt!")

  # Sauberer HTML-Download-Link (umgeht das iOS-Quick-Look-Problem)
  b64_excel = base64.b64encode(st.session_state.excel_data).decode()
  filename = st.session_state.filename
  href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{filename}" style="display: block; width: 100%; padding: 0.75rem; background-color: #FF4B4B; color: white; border-radius: 0.5rem; text-decoration: none; font-weight: bold; text-align: center; box-sizing: border-box; margin-bottom: 1rem;">📥 Excel-Datei herunterladen</a>'
  st.markdown(href, unsafe_allow_html=True)

  st.write("")
  if st.button("🔄 Nächsten Auftrag erfassen"):
    st.session_state.success_generated = False
    st.session_state.reset_trigger += 1
    st.rerun()

elif uploaded_file is None:
  st.info(
      "💡 Gib deine Rechnungsnummer (z. B. 191) ein und lade ein Foto des"
      " Auftragszettels hoch."
  )

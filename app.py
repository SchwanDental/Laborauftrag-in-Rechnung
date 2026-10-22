import datetime
from io import BytesIO
import json
import re
import openpyxl
from PIL import Image
import streamlit as st
from google import genai

import streamlit as st

if "AQ.Ab8RN6K-XiYBBX1WphYEst25KFmSw7mFeXvrjuQE-aE99Lsg4g" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]
else:
  api_key = st.sidebar.text_input("AQ.Ab8RN6K-XiYBBX1WphYEst25KFmSw7mFeXvrjuQE-aE99Lsg4g", type="password")

st.set_page_config(
    page_title="Schwan Dental Auftragszettel", page_icon="🦷", layout="centered"
)

st.title("🦷 Schwan Dental - Auftragszettel Scanner")
st.write(
    "Fotografiere den Zettel mit dem Handy oder lade ein Bild hoch. Die App"
    " trägt alles in deine Excel-Vorlage ein!"
)

# Sidebar für API-Key
with st.sidebar:
  st.header("⚙️ Einstellungen")
  api_key = st.text_input(
      "Google Gemini API Key",
      type="password",
      help=(
          "Kostenlos erhältlich auf aistudio.google.com (wird für die"
          " Texterkennung benötigt)"
      ),
  )
  st.markdown("---")
  st.markdown(
      "**Ziel-Zellen:**\n- **G9:** Datum\n- **G11:** Rechnungsnr.\n- **G12:**"
      " Patientenname\n- **G16:** XML-Nummer"
  )

# Bildaufnahme (Kamera oder Upload)
source_option = st.radio(
    "Bildquelle wählen:", ["Handy-Kamera", "Datei hochladen"]
)
uploaded_image = None

if source_option == "Handy-Kamera":
  uploaded_image = st.camera_input("Auftragszettel fotografieren")
else:
  uploaded_image = st.file_uploader(
      "Bild auswählen", type=["jpg", "jpeg", "png"]
  )

if uploaded_image is not None:
  image = Image.open(uploaded_image)
  st.image(image, caption="Aufgenommener Zettel", use_container_width=True)

  rechnung_nr = st.text_input("Rechnungsnummer (Zelle G11)", value="26.167")
  datum_input = st.date_input("Datum (Zelle G9)", value=datetime.date.today())

  if st.button("🚀 Daten auslesen & Excel befüllen", type="primary"):
    if not api_key:
      st.error(
          "Bitte gib zuerst deinen Gemini API Key in der Seitenleiste ein."
      )
    else:
      with st.spinner(
          "Analysiere Auftragszettel und befüllt Excel-Tabelle..."
      ):
        try:
          client = genai.Client(api_key=api_key)
          prompt = (
              "Analysiere diesen zahntechnischen Auftragszettel. "
              "Extrahiere zwei Werte im JSON-Format:\n"
              '1. "patientenname": Name des Patienten\n'
              '2. "xml_nummer": XML-Nummer bzw. Auftragsnummer (meist eine lange'
              " Nummer mit Bindestrichen)\n"
              "Antworte ausschließlich im JSON-Format."
          )

          response = client.models.generate_content(
              model="gemini-3.8-flash", contents=[image, prompt]
          )

          cleaned = (
              response.text.replace("```json", "")
              .replace("```", "")
              .strip()
          )
          data = json.loads(cleaned)

          p_name = data.get("patientenname", "Unbekannt")
          xml_num = data.get("xml_nummer", "")

          # Lädt deine Excel-Vorlage aus demselben Ordner
          wb = openpyxl.load_workbook("26.167_Rechnung.xlsx")
          sheet = wb.active

          sheet["G9"] = datum_input.strftime("%Y-%m-%d")
          sheet["G11"] = rechnung_nr
          sheet["G12"] = p_name
          sheet["G16"] = xml_num

          output = BytesIO()
          wb.save(output)
          output.seek(0)

          st.success("✅ Daten erfolgreich erkannt und eingetragen!")
          st.write(f"**Erkannter Patientenname (G12):** {p_name}")
          st.write(f"**Erkannte XML-Nummer (G16):** {xml_num}")

          st.download_button(
              label="📥 FERTIGE EXCEL HERUNTERLADEN",
              data=output,
              file_name=f"Rechnung_{rechnung_nr}_{p_name}.xlsx",
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
          )
        except Exception as e:
            st.error(f"Fehler bei der Auswertung: {e}")

import io
from google.oauth2 import service_account
import openpyxl
import streamlit as st
import vertexai
from PIL import Image as PILImage
from vertexai.generative_models import GenerativeModel, Image

# 1. Dienstkonto-Daten sicher aus den Streamlit Secrets laden
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# 2. Vertex AI mit dem Cloud-Guthaben starten
PROJECT_ID = "683856862514"
LOCATION = "us-central1"  # Serverstandort Frankfurt

vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# Modell initialisieren
model = GenerativeModel("gemini-1.5-pro")

# --- Benutzeroberfläche (Streamlit) ---
st.set_page_config(
    page_title="Dental Auftragszettel-Erfassung", page_icon="🦷", layout="centered"
)

st.title("🦷 Dental Auftragszettel-Erfassung")
st.write("Fotografiere den Zettel oder lade das Bild hoch.")

# Bild-Upload (unterstützt iPhone-Kamera direkt)
uploaded_file = st.file_uploader(
    "Zettel auswählen", type=["jpg", "jpeg", "png", "heic"]
)

if uploaded_file is not None:
  # Bild anzeigen
  image = PILImage.open(uploaded_file)
  st.image(image, caption="Aufgenommener Zettel", use_column_width=True)

  # Ausführen-Button
  if st.button("🚀 Daten auslesen & Excel befüllen"):
    try:
      with st.spinner(
          "Analysiere Auftragszettel über Google Cloud Vertex AI..."
      ):
        # Bild für Vertex AI aufbereiten
        img_byte_arr = io.BytesIO()
        img_format = image.format if image.format else "JPEG"
        image.save(img_byte_arr, format=img_format)
        img_bytes = img_byte_arr.getvalue()
        vertex_image = Image.from_bytes(img_bytes)

        # Dein Auswertungs-Prompt
        prompt = (
            "Analysiere diesen zahntechnischen Auftragszettel sorgfältig. "
            "Extrahiere die Rechnungsnummer (Zelle G11) und das Datum (Zelle G9) "
            "sowie alle relevanten Positionsangaben. "
            "Gib die Daten sauber und strukturiert aus."
        )

        # Anfrage an Vertex AI senden
        response = model.generate_content([vertex_image, prompt])
        extracted_text = response.text

      # Erfolg ausgeben
      st.success("Erfolgreich ausgelesen!")
      st.markdown("### Extrahierte Daten:")
      st.write(extracted_text)

    except Exception as e:
      st.error(f"Fehler bei der Auswertung: {e}")

import base64
from datetime import datetime
import glob
import io
import json
import os
from zoneinfo import ZoneInfo
import anthropic
import openpyxl
from openpyxl.styles import Alignment
import streamlit as st

# --- KONFIGURATION DEINES NAS-ORDNERS ---
NAS_ORDNER_PFAD = r"\\SchwanDental\Buchhaltung\Ausgangsrechnungen - Schwan Dental\2026"

os.makedirs(NAS_ORDNER_PFAD, exist_ok=True)

# Titel der Anwendung
st.title("🦷 Dental-Rechnungs-Generator (NAS-Automatik)")


# Funktion: Automatisch die nächste Rechnungsnummer ermitteln
def get_naechste_rechnungsnummer(ordner_pfad):
  suchmuster = os.path.join(ordner_pfad, "26.*_Rechnung.xlsx")
  gefundene_dateien = glob.glob(suchmuster)

  max_nr = 183  # Startwert als Fallback
  if gefundene_dateien:
    for datei in gefundene_dateien:
      dateiname = os.path.basename(datei)
      try:
        teil = dateiname.split("_")[0]
        nr = int(teil.split(".")[1])
        if nr > max_nr:
          max_nr = nr
      except Exception:
        pass

  naechste_nr = max_nr + 1
  return f"26.{naechste_nr}", naechste_nr


# Nächste Nummer automatisch aus dem NAS-Ordner berechnen
vollstaendige_rg_nr, rechnungs_int = get_naechste_rechnungsnummer(
    NAS_ORDNER_PFAD
)

# Session State initialisieren
if "reset_trigger" not in st.session_state:
  st.session_state.reset_trigger = 0

# Anzeige der automatisch ermittelten Rechnungsnummer
st.info(
    f"📌 Nächste automatische Rechnungsnummer: **{vollstaendige_rg_nr}** "
    f"(Verbunden mit Synology NAS ✅)"
)

# Laborauftrag fotografieren / hochladen
st.subheader("Laborauftrag fotografieren / hochladen")
uploaded_file = st.file_uploader(
    "Auftragszettel als Bild hochladen",
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.reset_trigger}",
)

if uploaded_file is not None:
  st.image(
      uploaded_file, caption="Aufgenommener Zettel", use_column_width=True
  )

  if st.button("🚀 Rechnung generieren & direkt auf Synology speichern"):
    with st.spinner(
        "Claude liest den Zettel aus und speichert direkt auf dem NAS..."
    ):
      try:
        # Bild in Base64 umwandeln
        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Anthropic Client initialisieren
        api_key = (
            st.secrets["ANTHROPIC_API_KEY"]
            if "ANTHROPIC_API_KEY" in st.secrets
            else os.environ.get("ANTHROPIC_API_KEY")
        )
        client = anthropic.Anthropic(api_key=api_key)

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

        # Feste Excel-Vorlage laden
        wb = openpyxl.load_workbook("Vorlage.xlsx")
        ws = wb.active

        # Zellen exakt nach Vorgabe belegen:
        deutsches_datum = (
            datetime.now(ZoneInfo("Europe/Berlin"))
            .date()
            .strftime("%d.%m.%Y")
        )
        ws["G9"] = deutsches_datum
        ws["G9"].alignment = Alignment(horizontal="right")

        ws["G11"] = vollstaendige_rg_nr  # z.B. 26.191
        ws["G12"] = patientenname  # Patientenname
        ws["G16"] = auftragsnummer  # XML-Auftragsnummer

        # Direkt auf der Synology NAS speichern!
        ziel_dateiname = f"{vollstaendige_rg_nr}_Rechnung.xlsx"
        ziel_pfad = os.path.join(NAS_ORDNER_PFAD, ziel_dateiname)
        wb.save(ziel_pfad)

        st.success(
            f"✅ Erfolgreich generiert und direkt auf der Synology abgelegt"
            f" unter:\n`{ziel_pfad}`"
        )
        st.session_state.success_saved = True

      except Exception as e:
        st.error(f"Fehler bei der Verarbeitung: {e}")

# Wenn erfolgreich gespeichert, Button für den nächsten Auftrag (Korrektur: st.session_state.get)
if st.session_state.get("success_saved", False):
  if st.button("🔄 Nächsten Auftrag erfassen"):
    st.session_state.success_saved = False
    st.session_state.reset_trigger += 1
    st.rerun()

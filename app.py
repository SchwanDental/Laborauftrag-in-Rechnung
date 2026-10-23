import base64
import anthropic
import streamlit as st

# Titel der Anwendung
st.title("🦷 Dental-Auftrag Auswertung")

# Dateiupload für das Bild
uploaded_file = st.file_uploader(
    "Laborauftrag fotografieren / hochladen", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  # Das hochgeladene Bild anzeigen
  st.image(
      uploaded_file, caption="Aufgenommener Zettel", use_column_width=True
  )

  if st.button("🚀 Daten auslesen & Excel befüllen"):
    with st.spinner("Claude analysiert den Zettel..."):
      try:
        # Bild in Base64 umwandeln
        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Anthropic Client initialisieren
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

        # Anfrage an Claude senden
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
                        {
                            "type": "text",
                            "text": (
                                "Analysiere diesen zahnärztlichen Laborauftrag"
                                " exakt. Extrahiere alle wichtigen Daten"
                                " (Patientenname, Geburtsdatum, Auftragsnummer,"
                                " Zahnstatus/Befund und geplante Arbeiten)"
                                " und gib sie übersichtlich als strukturierte"
                                " Liste zurück."
                            ),
                        },
                    ],
                }
            ],
        )

        # Ergebnis sicher aus den Content-Blöcken extrahieren (ignoriert Thinking-Blöcke)
        result_text = ""
        for block in message.content:
          if hasattr(block, "text"):
            result_text += block.text

        st.success("Erfolgreich ausgelesen!")
        st.markdown(result_text)

      except Exception as e:
        st.error(f"Fehler bei der Auswertung: {e}")

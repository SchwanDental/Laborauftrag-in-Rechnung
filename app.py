import base64
import anthropic
import streamlit as st

# Streamlit UI Setup
st.title("🦷 Dental-Auftrag Auswertung")

uploaded_file = st.file_uploader(
    "Laborauftrag fotografieren / hochladen", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  # Bild anzeigen
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

        # Anfrage an Claude 3.5 Haiku senden (garantiert für alle Accounts freigeschaltet)
        message = client.messages.create(
            model="claude-3-5-haiku-20240307",
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
                                " Zahnstatus/Befund und geplante Arbeiten) und"
                                " gib sie übersichtlich als strukturierte"
                                " Liste zurück."
                            ),
                        },
                    ],
                }
            ],
        )

        # Ergebnis anzeigen
        result_text = message.content[0].text
        st.success("Erfolgreich ausgelesen!")
        st.markdown(result_text)

      except Exception as e:
        st.error(f"Fehler bei der Auswertung: {e}")

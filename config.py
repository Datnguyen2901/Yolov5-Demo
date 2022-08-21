from streamlit_webrtc import ClientSettings

CLASSES = ['Bird', 'Cat', 'Dog', 'Monkey', 'Squirrel']


WEBRTC_CLIENT_SETTINGS = ClientSettings(
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
    )
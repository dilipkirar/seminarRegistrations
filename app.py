import socket
import gradio as gr
from src.ui import build_demo, CUSTOM_CSS
from src.config import SERVER_HOST, DEFAULT_PORT


def find_available_port(preferred_port: int = DEFAULT_PORT) -> int:
    """Finds an available local port starting from preferred_port."""
    for port in [preferred_port, 7862, 7865, 7870, 8080, 8501, 8888]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((SERVER_HOST, port))
                return port
            except OSError:
                continue
    return preferred_port


def main():
    demo = build_demo()
    port = find_available_port(DEFAULT_PORT)
    print(f"\n🚀 Launching AutoTrain AI Seminar System on: http://{SERVER_HOST}:{port}\n")

    demo.launch(
        server_name=SERVER_HOST,
        server_port=port,
        theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="slate"),
        css=CUSTOM_CSS,
        share=False,
    )


if __name__ == "__main__":
    main()

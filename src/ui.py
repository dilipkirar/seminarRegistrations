import gradio as gr
from src.database import load_file_seminars
from src.agent import chat_with_agent
from src.email_service import send_confirmation_email

# Modern Responsive Mobile-First CSS
CUSTOM_CSS = """
.gradio-container {
    max-width: 980px !important;
    margin: 0 auto !important;
    padding: 16px !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

@media (max-width: 640px) {
    .gradio-container {
        padding: 8px !important;
    }
}

.hero-box {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    color: #ffffff;
    padding: 24px 20px;
    border-radius: 16px;
    margin-bottom: 18px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(49, 46, 129, 0.15);
}

.hero-box h1 {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-bottom: 6px !important;
}

.hero-box p {
    color: #c7d2fe !important;
    font-size: 0.95rem !important;
}

.card-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px;
    margin-top: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.action-btn {
    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 1rem !important;
}
"""


def submit_final_form(name, email, seminar_id, confirmed_date):
    """Trigger final confirmation email alert from manual tab form."""
    if not name or not name.strip():
        return "⚠️ Please enter your Full Name."
    if not email or "@" not in email:
        return "⚠️ Please enter a valid Email Address."
    if not seminar_id or not seminar_id.strip():
        return "⚠️ Please select a Seminar."

    df = load_file_seminars()
    row = df[df["id"] == seminar_id.strip()]
    if row.empty:
        return f"⚠️ Seminar ID '{seminar_id}' not found in database."

    sem = row.iloc[0].to_dict()
    if sem["status"] != "Open":
        return f"⚠️ Seminar {seminar_id} ({sem['title']}) is Closed."

    success, status = send_confirmation_email(name.strip(), email.strip(), sem)

    if success:
        return (
            f"🎉 REGISTRATION CONFIRMED for {name}!\n"
            f"Seminar: {sem['title']} ({sem['id']}) on {confirmed_date}\n"
            f"Email Alert: {status}"
        )
    else:
        return f"Registration recorded for {name}, but email failed: {status}"


def populate_form_from_selection(selected_id):
    """Auto-fills form fields when user picks a seminar from dropdown."""
    df = load_file_seminars()
    row = df[df["id"] == selected_id]
    if not row.empty:
        r = row.iloc[0]
        return r["id"], r["date"]
    return "SEM-101", "2026-01-02"


def build_demo() -> gr.Blocks:
    """Builds the complete Gradio interface with 3 responsive tabs."""
    df_initial = load_file_seminars()
    open_choices = [
        (f"{r['id']} [{r['date']}] - {r['title']} ({r['city']}, {r['state']})", r["id"])
        for _, r in df_initial[df_initial["status"] == "Open"].iterrows()
    ]

    with gr.Blocks(title="AutoTrain AI – India Seminar Booking") as demo:
        # Header Banner
        gr.HTML(
            """
            <div class="hero-box">
                <h1>🇮🇳 AutoTrain AI – India Seminar Registration System</h1>
                <p>Dynamic AI Generation via Google GenAI + 100+ Scheduled Seminars Across All Months of 2026</p>
            </div>
            """
        )

        with gr.Tab("💬 AI Conversational Assistant (Recommended)"):
            gr.Markdown(
                "### 🧭 Quick Booking in 3 Messages:\n"
                "1. Enter any month or travel dates & location *(e.g. `In March in Maharashtra`, `In July in Gujarat`, `October in Bangalore`)*\n"
                "2. Type your chosen option number *(e.g. `1`, `2`, or `3`)*\n"
                "3. Enter your Name & Email, review verification preview, and reply **'Confirm'** to get your email pass!"
            )
            gr.ChatInterface(fn=chat_with_agent)

        with gr.Tab("📝 Instant Registration Form"):
            with gr.Column(elem_classes=["card-container"]):
                gr.Markdown("### Manual One-Click Registration")
                gr.Markdown("Pick an upcoming session from 100+ open seminars:")

                picker = gr.Dropdown(
                    label="Select Available Open Seminar",
                    choices=open_choices,
                    value=open_choices[0][1] if open_choices else None,
                )

                with gr.Row():
                    u_name = gr.Textbox(
                        label="Full Name",
                        placeholder="Enter your name (e.g. Dilip Kirar)",
                        scale=1,
                        min_width=260,
                    )
                    u_email = gr.Textbox(
                        label="Email Address (Confirmation will be sent here)",
                        value="enggdilipkirar@gmail.com",
                        scale=1,
                        min_width=260,
                    )

                with gr.Row():
                    u_sem_id = gr.Textbox(
                        label="Seminar ID",
                        value=open_choices[0][1] if open_choices else "SEM-101",
                        scale=1,
                        min_width=260,
                    )
                    u_date = gr.Textbox(
                        label="Seminar Date (YYYY-MM-DD)",
                        value="2026-01-02",
                        scale=1,
                        min_width=260,
                    )

                picker.change(
                    fn=populate_form_from_selection,
                    inputs=[picker],
                    outputs=[u_sem_id, u_date],
                )

                submit_btn = gr.Button(
                    "Confirm Date & Send Email Pass 🚀",
                    variant="primary",
                    elem_classes=["action-btn"],
                )

                status_box = gr.Textbox(
                    label="Booking & Email Dispatch Status",
                    lines=4,
                    placeholder="Real-time confirmation status and Gmail alert delivery receipt will appear here.",
                )

                submit_btn.click(
                    fn=submit_final_form,
                    inputs=[u_name, u_email, u_sem_id, u_date],
                    outputs=[status_box],
                )

        with gr.Tab("📅 India Seminars Master Schedule (100+ Events)"):
            with gr.Column(elem_classes=["card-container"]):
                gr.Markdown("### Full Schedule Across All 12 Months of 2026")
                gr.Markdown("Browse all scheduled sessions by date, city, and status:")
                gr.DataFrame(
                    value=df_initial[["id", "date", "title", "state", "city", "university", "type", "status"]],
                    headers=["ID", "Date", "Title", "State", "City", "University", "Type", "Status"],
                    interactive=False,
                )

    return demo

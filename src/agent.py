import re
from typing import Dict, Any, List
from src.parser import parse_dates_and_location
from src.database import get_seminars
from src.email_service import send_confirmation_email

# Session state dictionary for conversational flow
session_state: Dict[str, Any] = {
    "step": "ASK_SEARCH",  # ASK_SEARCH -> SHOW_OPTIONS -> ASK_DETAILS -> VERIFY -> CONFIRMED
    "matching_seminars": [],
    "selected_seminar": None,
    "user_name": "",
    "user_email": "",
}


def reset_session():
    """Resets conversational state for a fresh search."""
    session_state["step"] = "ASK_SEARCH"
    session_state["matching_seminars"] = []
    session_state["selected_seminar"] = None
    session_state["user_name"] = ""
    session_state["user_email"] = ""


async def chat_with_agent(user_message: str, history: List = None) -> str:
    """
    Step-by-step India Seminar Registration Agent:
    1. Travel dates (any month) + state/city -> Filter & show numbered options (1, 2, 3...)
    2. User picks option -> Verify if Open
    3. User gives Name & Email -> Format verification review
    4. User confirms -> Send confirmation email pass via Gmail SMTP
    """
    msg = user_message.strip() if user_message else ""
    lower_msg = msg.lower()

    # Empty / whitespace input handling
    if not msg:
        return (
            "👋 **Welcome!** Please provide your travel dates (or month) and location in India:\n"
            "*(Examples: `In March in Maharashtra`, `April to June in Gujarat`, `From 2026-08-01 to 2026-08-30 in Bangalore`)*"
        )

    # Session reset command handling
    if lower_msg in ["restart", "reset", "start again", "cancel", "new search", "clear"]:
        reset_session()
        return (
            "🔄 **Search Reset.**\n\n"
            "Please provide your travel dates (or month) and location in India:\n"
            "*(Examples: `In March in Maharashtra`, `April to June in Gujarat`, `From 2026-08-01 to 2026-08-30 in Bangalore`)*"
        )

    current_step = session_state["step"]

    # --------------------------------------------------------------------------
    # STEP 1: Search Seminars by Month/Dates & State or City (AI + DB Provider)
    # --------------------------------------------------------------------------
    if current_step == "ASK_SEARCH" or len(session_state["matching_seminars"]) == 0:
        from_date, to_date, location, is_foreign = parse_dates_and_location(msg)

        # Foreign location check (India-only portal)
        if is_foreign:
            return (
                f"🇮🇳 **India-Only Seminar Portal:**\n\n"
                f"We currently only host seminars in **India** and do not have listings for **'{location.title()}'**.\n\n"
                f"Please search for an Indian state or city, such as:\n"
                f"• `Maharashtra` (Pune, Mumbai)\n"
                f"• `Gujarat` (Ahmedabad, Surat)\n"
                f"• `Karnataka` (Bangalore)\n"
                f"• `Delhi` (New Delhi)\n"
                f"• `Madhya Pradesh` (Bhopal, Indore)"
            )

        # Use AI dynamic generation if available, otherwise file database
        df_results = get_seminars(from_date, to_date, location, use_ai=False)

        if df_results.empty:
            return (
                f"🔍 No seminars found for **'{location or 'specified location'}'** between **{from_date}** and **{to_date}**.\n\n"
                f"💡 **We have 100+ seminars across all months in India!**\n"
                f"Try searching by month or state, for example:\n"
                f"• `In March in Maharashtra`\n"
                f"• `In July in Gujarat`\n"
                f"• `September in Bangalore`\n"
                f"• `October to December in Delhi`"
            )

        matching_list = df_results.to_dict(orient="records")
        session_state["matching_seminars"] = matching_list
        session_state["step"] = "SHOW_OPTIONS"

        options_text = ""
        # Display top 8 options to keep interface clean and responsive
        displayed_items = matching_list[:8]
        for i, sem in enumerate(displayed_items, 1):
            status_icon = "🟢" if sem["status"] == "Open" else "🔴"
            options_text += (
                f"\n**{i}. [{sem['id']}] {sem['title']}**\n"
                f"   • 📍 **Location:** {sem['city']}, {sem['state']} ({sem['university']})\n"
                f"   • 📅 **Date:** {sem['date']} ({sem['type']})\n"
                f"   • 🏷️ **Status:** {status_icon} **{sem['status']}**\n"
            )

        more_note = f"\n*(+ {len(matching_list) - 8} more matching seminars in schedule tab)*\n" if len(matching_list) > 8 else ""
        loc_label = f" in {location.title()}" if location else " in India"

        return (
            f"🎓 **Found {len(matching_list)} Seminars{loc_label} ({from_date} to {to_date}):**\n"
            f"{options_text}{more_note}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 **Please choose an option by typing its number (e.g. 1, 2, or 3):**"
        )

    # --------------------------------------------------------------------------
    # STEP 2: Handle Option Selection
    # --------------------------------------------------------------------------
    if current_step == "SHOW_OPTIONS":
        digit_match = re.search(r"\b(\d+)\b", msg)
        choice_idx = -1

        if digit_match:
            choice_idx = int(digit_match.group(1)) - 1
        elif msg.upper().startswith("SEM-"):
            for idx, s in enumerate(session_state["matching_seminars"]):
                if s["id"].upper() == msg.upper():
                    choice_idx = idx
                    break

        if 0 <= choice_idx < len(session_state["matching_seminars"]):
            selected = session_state["matching_seminars"][choice_idx]

            if selected["status"] != "Open":
                return (
                    f"⚠️ **Option {choice_idx + 1} ({selected['title']}) is CLOSED.**\n"
                    f"Please choose an **Open** seminar from the list (e.g. type another number):"
                )

            session_state["selected_seminar"] = selected
            session_state["step"] = "ASK_DETAILS"

            return (
                f"✅ **You selected:**\n"
                f"**[{selected['id']}] {selected['title']}**\n"
                f"• 📅 **Date:** {selected['date']} ({selected['type']})\n"
                f"• 📍 **Venue:** {selected['university']}, {selected['city']}, {selected['state']}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 **Now please provide your details for registration:**\n"
                f"Please reply with your **Full Name** and **Email Address**.\n\n"
                f"*(Example: `Dilip Kirar, enggdilipkirar@gmail.com`)*"
            )
        else:
            total = min(8, len(session_state["matching_seminars"]))
            return f"⚠️ Invalid option. Please enter a number between **1 and {total}**:"

    # --------------------------------------------------------------------------
    # STEP 3: Collect Details & Present Verification Card
    # --------------------------------------------------------------------------
    if current_step == "ASK_DETAILS":
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", msg)
        user_email = email_match.group(0) if email_match else ""

        if user_email:
            cleaned = msg.replace(user_email, "").strip(" ,:-")
            user_name = cleaned if cleaned else "Dilip Kirar"
        else:
            user_name = msg.strip()
            user_email = "enggdilipkirar@gmail.com"

        session_state["user_name"] = user_name
        session_state["user_email"] = user_email
        session_state["step"] = "VERIFY"

        sem = session_state["selected_seminar"]
        return (
            f"📋 **Please Verify Your Registration Details:**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• 👤 **Full Name:** {user_name}\n"
            f"• ✉️ **Email Address:** {user_email}\n"
            f"• 🎓 **Seminar ID:** `{sem['id']}`\n"
            f"• 📌 **Seminar Title:** {sem['title']}\n"
            f"• 📅 **Scheduled Date:** {sem['date']} ({sem['type']})\n"
            f"• 🏛️ **University / Venue:** {sem['university']}, {sem['city']}, {sem['state']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👉 Reply **'Confirm'** (or **'Yes'**) to finalize and dispatch your official email pass!\n"
            f"*(Or reply **'Cancel'** to start a new search)*"
        )

    # --------------------------------------------------------------------------
    # STEP 4: Confirm Registration and Send Email Pass
    # --------------------------------------------------------------------------
    if current_step == "VERIFY":
        if any(w in lower_msg for w in ["confirm", "yes", "ha", "haan", "ok", "done", "proceed"]):
            name = session_state["user_name"]
            email = session_state["user_email"]
            sem = session_state["selected_seminar"]

            success, email_status = send_confirmation_email(name, email, sem)
            session_state["step"] = "CONFIRMED"

            return (
                f"🎉 **CONGRATULATIONS! REGISTRATION CONFIRMED** 🎉\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• **Attendee:** {name}\n"
                f"• **Registration Pass:** `REG-2026-{sem['id']}`\n"
                f"• **Seminar:** {sem['title']}\n"
                f"• **Date:** {sem['date']} ({sem['type']})\n"
                f"• **Venue:** {sem['university']}, {sem['city']}, {sem['state']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📧 **Email Status:** {email_status}\n\n"
                f"*(To book another seminar in a different month, type `new search`)*"
            )
        else:
            return "Please reply **'Confirm'** to send the email pass, or **'Cancel'** to choose a different seminar."

    if current_step == "CONFIRMED":
        reset_session()
        return (
            "👋 **Ready for a new search!**\n\n"
            "Please enter your travel dates or month and Indian location:\n"
            "*(Example: `In July in Pune` or `2026-09-01 to 2026-09-30 in Bangalore`)*"
        )

    return "Please tell me your travel month/dates and destination city or state."

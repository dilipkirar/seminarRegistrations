# seminarRegistrations
AutoTrain AI – India Seminar Registration System
# 🇮🇳 India Seminar AI Agent

An intelligent conversational AI agent built with **Google GenAI (Gemini)**, **Gradio**, and **Gmail SMTP**, designed to discover, recommend, verify, and register for university seminars across all Indian states and cities.

---

## 📁 Project Architecture

```
india-seminar-agent/
│
├── .env                        # Secret API keys aur email passwords
├── .env.example                # Dummy template (GitHub par upload karne ke liye)
├── .gitignore                  # .env aur cache files ko ignore karne ke liye
├── requirements.txt            # Project ki sabhi Python libraries
├── README.md                   # Project setup aur run karne ki guide
├── app.py                      # Main entry point (sirf app launch karega)
│
├── data/
│   ├── seminars_data.json      # Master database (120+ seminars across 12 months)
│   └── seminars_data.csv       # Spreadsheet CSV export
│
└── src/                        # Main source code folder
    ├── __init__.py
    ├── config.py               # Environment variables aur constants
    ├── database.py             # Google GenAI dynamic generation + local fallback
    ├── parser.py               # Date, month (Jan-Dec) aur Indian city/state parser
    ├── email_service.py        # Gmail SMTP SSL email bhejne ka logic
    ├── agent.py                # 4-step chatbot state machine
    └── ui.py                   # Responsive Gradio layout, tabs aur custom CSS
```

---

## 🤖 Dynamic AI Model Generation vs. File Reading

This system supports **BOTH**:
1. **Dynamic Google GenAI Discovery:** When a user queries travel dates and an Indian location, `src/database.py` can call Gemini (`google.genai`) to generate and format matching seminars dynamically on the fly in the exact same schema.
2. **Zero-Error Local Fallback:** If the Gemini API is temporarily busy, offline, or rate-limited, it automatically falls back to the **127+ scheduled seminars** in `data/seminars_data.json` spanning all 12 months of 2026. This guarantees **100% uptime with 0 runtime errors**.

---

## 🚀 How to Run the Project

1. **Install requirements:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure your credentials in `.env`:**
   ```env
   GEMINI_API_KEY=YOUR_FREE_GEMINI_API_KEY
   SENDER_EMAIL=your_email@gmail.com
   APP_PASSWORD=your_16_char_gmail_app_password
   ```

3. **Start the application:**
   ```powershell
   python app.py
   ```

4. Open your browser at:
   👉 **`http://127.0.0.1:7861`**

---

## 🧭 Conversational Flow in 3 Messages:

1. **Travel Dates & Location:** Enter travel month/dates and destination (e.g., `In March in Maharashtra` or `July to September in Bangalore`).
2. **Option Selection:** Pick your preferred seminar by number (`1`, `2`, or `3`).
3. **Verify & Confirm:** Enter your Name & Email. Review the verification card, then reply **`Confirm`** to immediately receive your official seminar pass via Gmail!


# Professor Outreach

> AI-powered professor discovery and personalized cold email outreach platform for research students seeking collaboration opportunities.

**[Live Demo](https://professor-outreach.onrender.com)** | **[Portfolio](https://github.com/ishanvireddy71)**

---

## What This Is

A Flask-based web application that automates the entire professor outreach pipeline:

1. **Discovers real professors** from target universities using curated fallback data
2. **Guesses academic email patterns** (`firstname.lastname@mit.edu`) with MX validation
3. **Generates personalized cold emails** using GPT-4o-mini with human-like templates as fallback
4. **Sends emails via Gmail SMTP** with test mode safety gate
5. **Detects bounces** via IMAP inbox scanning

Built for students who want to reach out to professors for research opportunities but struggle with finding contacts and writing personalized emails.

---

## Features

| Feature | Status |
|---------|--------|
| Professor Discovery (10+ universities) | Done |
| Smart Email Pattern Guessing + MX Validation | Done |
| AI Email Generation (GPT-4o-mini) | Done |
| Real Gmail SMTP Sending | Done |
| IMAP Bounce Detection | Done |
| Analytics Dashboard | Done |
| CSV/JSON Data Export | Done |
| Bulk Approve/Reject | Done |
| Email Scheduling | Done |
| Advanced Search | Done |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.1.0 |
| Database | SQLite3 |
| AI | OpenAI GPT-4o-mini |
| Email | smtplib (SMTP), imaplib (IMAP), dnspython |
| Security | Werkzeug password hashing, python-dotenv |
| Frontend | HTML5, CSS3, Jinja2 Templates |
| Deploy | Render (Gunicorn) |

---

## Run Locally

**Requirements:** Python 3.11+

**1. Clone**

```bash
git clone https://github.com/ishanvireddy71/professor-outreach.git
cd professor-outreach
```

**2. Create virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment**

Create a `.env` file in the project root:

```bash
SECRET_KEY=your-random-key
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
OPENAI_API_KEY=your_openai_key
```

**5. Run**

```bash
python app.py
```

Open http://localhost:5000

---

## How to Use

1. **Sign up** at `/signup`
2. **Configure settings** - your name, university, research topic, target universities
3. **Run the pipeline** from Dashboard:
   - Discover Professors
   - Find Emails
   - Generate Emails
   - Send Emails (toggle test mode off for real sending)

**Test Mode vs Real Sending:**

- **Test Mode ON** (default): Emails marked sent but not actually sent. Use for preview.
- **Test Mode OFF**: Emails sent via Gmail SMTP. Requires valid `.env` credentials.

---

## Repository Structure

```
.
├── app.py                 # Flask server
├── config.py              # Config module
├── config.json            # App settings (no secrets)
├── .env                   # Secrets (not committed)
├── requirements.txt       # Dependencies
├── modules/
│   ├── database.py        # SQLite setup
│   ├── discovery.py       # Professor discovery
│   ├── email_finder.py    # Pattern guessing + MX validation
│   ├── personalization.py # AI email generation
│   ├── sender.py          # SMTP sending
│   └── bounce_detector.py # IMAP bounce check
├── static/                # CSS, JS
├── templates/             # HTML templates
└── professor_outreach.db  # SQLite database
```

---

## Configuration

All user settings in `config.json`:

```json
{
  "your_name": "Ishanvi",
  "your_email": "ishanvireddy79@gmail.com",
  "your_university": "Koneru Lakshmaiah Education Foundation",
  "research_topic": "Machine Learning, Deep Learning",
  "target_universities": ["MIT", "Stanford", "CMU", "Berkeley", "Harvard"],
  "test_mode": true
}
```

Secrets live only in `.env` - never in `config.json`.

---

## Deployment

### Render (Free Tier)

1. Push to GitHub (`.env` is in `.gitignore`)
2. Connect repo on [render.com](https://render.com)
3. Add environment variables in Render dashboard
4. Deploy

**Note:** Render free tier has ephemeral filesystem - SQLite resets on redeploy.

---

## Author

**Ishanvi Reddy** - B.Tech AI & Data Science, KL University

GitHub: [ishanvireddy71](https://github.com/ishanvireddy71) | Email: ishanvireddy79@gmail.com

---

## License

MIT
"""Send emails via real SMTP with test_mode gating."""
import sqlite3
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = 'professor_outreach.db'


def _get_smtp_config():
    """Load SMTP credentials from environment only."""
    return {
        'user': os.environ.get('GMAIL_USER', ''),
        'password': os.environ.get('GMAIL_APP_PASSWORD', ''),
        'host': 'smtp.gmail.com',
        'port': 587,
    }


def run(test_mode=True):
    """Send ready emails via SMTP. Respects test_mode to gate real sends."""
    config = _get_smtp_config()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id, e.subject, e.body, p.email, p.name
        FROM emails e
        JOIN professors p ON e.professor_id = p.id
        WHERE e.status = 'ready'
    """)

    rows = cursor.fetchall()
    if not rows:
        print("[Sender] No ready emails to send.")
        conn.close()
        return

    smtp_conn = None
    if not test_mode:
        if not config['user'] or not config['password']:
            print("[Sender] ERROR: Gmail credentials not set in .env. Cannot send real emails.")
            conn.close()
            return
        try:
            smtp_conn = smtplib.SMTP(config['host'], config['port'])
            smtp_conn.starttls()
            smtp_conn.login(config['user'], config['password'])
            print(f"[Sender] Connected to {config['host']}:{config['port']} as {config['user']}")
        except Exception as e:
            print(f"[Sender] ERROR: SMTP connection failed: {e}")
            conn.close()
            return

    sent = 0
    for row in rows:
        if test_mode:
            print(f"[Sender] TEST MODE: Would send to {row['name']} <{row['email']}>")
            cursor.execute("UPDATE emails SET status = 'sent' WHERE id = ?", (row['id'],))
            sent += 1
        else:
            try:
                msg = MIMEMultipart()
                msg['From'] = config['user']
                msg['To'] = row['email']
                msg['Subject'] = row['subject']
                msg.attach(MIMEText(row['body'], 'plain'))
                smtp_conn.send_message(msg)
                print(f"[Sender] SENT: {row['name']} <{row['email']}>")
                cursor.execute("UPDATE emails SET status = 'sent' WHERE id = ?", (row['id'],))
                sent += 1
                # Respect delay between emails from config
                delay = int(os.environ.get('DELAY_BETWEEN_EMAILS', '60'))
                if delay > 0:
                    time.sleep(delay)
            except Exception as e:
                print(f"[Sender] FAILED: {row['name']} <{row['email']}> - {e}")

    if smtp_conn:
        try:
            smtp_conn.quit()
        except:
            pass

    conn.commit()
    conn.close()
    mode_str = "TEST" if test_mode else "REAL"
    print(f"[Sender] {mode_str} mode: Processed {sent} emails")
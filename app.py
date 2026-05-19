from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os
import csv
import io
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from modules.database import init_db, create_user, get_user_by_username, user_exists, DB_FILE

# Load .env early
from dotenv import load_dotenv
load_dotenv()

# ==================== PIPELINE IMPORTS (MOVED TO TOP) ====================

try:
    from modules.discovery import discover_all_professors
    DISCOVERY_AVAILABLE = True
except Exception as e:
    DISCOVERY_AVAILABLE = False
    print(f"[WARN] Discovery module not available: {e}")

try:
    from modules.email_finder import run as run_email_finder
    EMAIL_FINDER_AVAILABLE = True
except Exception as e:
    EMAIL_FINDER_AVAILABLE = False
    print(f"[WARN] Email finder module not available: {e}")

try:
    from modules.personalization import run as run_personalization
    PERSONALIZATION_AVAILABLE = True
except Exception as e:
    PERSONALIZATION_AVAILABLE = False
    print(f"[WARN] Personalization module not available: {e}")

try:
    from modules.sender import run as run_sender
    SENDER_AVAILABLE = True
except Exception as e:
    SENDER_AVAILABLE = False
    print(f"[WARN] Sender module not available: {e}")

try:
    from modules.bounce_detector import check_bounces, get_bounce_stats
    BOUNCE_AVAILABLE = True
except Exception as e:
    BOUNCE_AVAILABLE = False
    print(f"[WARN] Bounce detector not available: {e}")

# ==================== INIT ====================

init_db(verbose=False)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'professor-outreach-secret-key-2024-change-in-production')
app.config['TEMPLATES_AUTO_RELOAD'] = True

DB_PATH = 'professor_outreach.db'


def get_db():
    """Get SQLite connection with thread safety."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def load_config():
    """Load config from config.json with defaults."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        config = {}
    defaults = {
        "your_name": "User",
        "your_email": "your.email@example.com",
        "your_university": "Your Institution",
        "your_major": "",
        "your_year": "",
        "research_topic": "Research",
        "target_universities": ["University"],
        "emails_per_university": 5,
        "max_emails_per_day": 10,
        "delay_between_emails": 60,
        "test_mode": True,
        "gmail_user": "",
        "gmail_app_password": "",
        "openai_api_key": ""
    }
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    return config


def save_config(config):
    """Save config to config.json."""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}")
        return False


# ==================== AUTH ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not user_exists():
        return redirect(url_for('signup'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('signup.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return render_template('signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        password_hash = generate_password_hash(password)
        success = create_user(username, password_hash)

        if success:
            flash('Account created! Please sign in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Choose a different one.', 'error')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== DASHBOARD ====================

@app.route('/')
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM professors")
    total_professors = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as with_email FROM professors WHERE email IS NOT NULL AND email != ''")
    with_email = cursor.fetchone()['with_email']
    cursor.execute("SELECT COUNT(*) as without_email FROM professors WHERE email IS NULL OR email = ''")
    without_email = cursor.fetchone()['without_email']
    cursor.execute("SELECT COUNT(*) as generated FROM emails")
    emails_generated = cursor.fetchone()['generated']
    cursor.execute("SELECT COUNT(*) as ready FROM emails WHERE status = 'ready'")
    ready_to_send = cursor.fetchone()['ready']
    cursor.execute("SELECT COUNT(*) as sent FROM emails WHERE status = 'sent'")
    sent_count = cursor.fetchone()['sent']
    conn.close()

    config = load_config()
    stats = {
        'your_name': config.get('your_name', 'User'),
        'research_topic': config.get('research_topic', 'Research'),
        'target_universities': config.get('target_universities', ['University']),
        'your_email': config.get('your_email', 'your.email@example.com'),
        'your_institution': config.get('your_university', 'Your Institution'),
        'total_professors': total_professors,
        'with_email': with_email,
        'without_email': without_email,
        'emails_generated': emails_generated,
        'ready_to_send': ready_to_send,
        'sent_count': sent_count
    }
    return render_template('dashboard.html', stats=stats)


# ==================== PROFESSORS ====================

@app.route('/professors')
@login_required
def professors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professors ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return render_template('professors.html', professors=rows)


@app.route('/api/approve-professor/<int:id>', methods=['POST'])
@login_required
def approve_professor(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE professors SET approved = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/reject-professor/<int:id>', methods=['POST'])
@login_required
def reject_professor(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE professors SET approved = 0 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== EMAILS ====================

@app.route('/emails')
@login_required
def emails():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, p.name as professor_name, p.university, p.email as professor_email, p.department
        FROM emails e
        LEFT JOIN professors p ON e.professor_id = p.id
        ORDER BY e.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    emails_list = []
    for row in rows:
        emails_list.append({
            'id': row['id'],
            'professor_id': row['professor_id'],
            'professor_name': row['professor_name'],
            'university': row['university'],
            'professor_email': row['professor_email'],
            'department': row['department'],
            'subject': row['subject'],
            'body': row['body'],
            'status': row['status'],
            'created_at': row['created_at']
        })
    return render_template('emails.html', emails=emails_list)


@app.route('/api/email/<int:id>', methods=['GET'])
@login_required
def get_email(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, p.name as professor_name, p.email as professor_email, p.university, p.department
        FROM emails e
        LEFT JOIN professors p ON e.professor_id = p.id
        WHERE e.id = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'error': 'Email not found'}), 404
    return jsonify({
        'success': True,
        'email': {
            'id': row['id'],
            'professor_name': row['professor_name'],
            'professor_email': row['professor_email'],
            'university': row['university'],
            'department': row['department'],
            'subject': row['subject'],
            'body': row['body'],
            'status': row['status']
        }
    })


@app.route('/api/email/<int:id>/update', methods=['POST'])
@login_required
def update_email(id):
    data = request.get_json(silent=True) or {}
    subject = data.get('subject', '')
    body = data.get('body', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE emails SET subject = ?, body = ?, updated_at = ?
        WHERE id = ?
    """, (subject, body, datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Email updated'})


@app.route('/api/email/<int:id>/regenerate', methods=['POST'])
@login_required
def regenerate_email(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.professor_id, p.name, p.university, p.research_interests, p.department
        FROM emails e
        JOIN professors p ON e.professor_id = p.id
        WHERE e.id = ?
    """, (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Email not found'}), 404

    config = load_config()

    from modules.personalization import generate_email_content

    new_subject = f"Research inquiry: {config.get('research_topic', 'Research')} and {row['research_interests'] or 'your work'}"
    new_body = generate_email_content(
        row['name'], row['university'], row['department'], row['research_interests'],
        config.get('your_name', 'Your Name'),
        config.get('your_university', 'Your Institution'),
        config.get('your_email', 'your.email@example.com'),
        config.get('research_topic', 'Research')
    )
    cursor.execute("""
        UPDATE emails SET subject = ?, body = ?, updated_at = ?
        WHERE id = ?
    """, (new_subject, new_body, datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({
        'success': True,
        'message': 'Email regenerated',
        'subject': new_subject,
        'body': new_body
    })


@app.route('/api/email/<int:id>/toggle-ready', methods=['POST'])
@login_required
def toggle_ready(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM emails WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Email not found'}), 404
    new_status = 'ready' if row['status'] == 'draft' else 'draft'
    cursor.execute("UPDATE emails SET status = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()
    return jsonify({
        'success': True,
        'message': f'Email marked as {new_status}',
        'status': new_status
    })


# ==================== SEND QUEUE ====================

@app.route('/send-queue')
@login_required
def send_queue():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, p.name as professor_name, p.university, p.email as professor_email, p.department
        FROM emails e
        LEFT JOIN professors p ON e.professor_id = p.id
        WHERE e.status = 'ready'
        ORDER BY e.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    emails_list = []
    for row in rows:
        emails_list.append({
            'id': row['id'],
            'professor_name': row['professor_name'],
            'university': row['university'],
            'professor_email': row['professor_email'],
            'department': row['department'],
            'subject': row['subject'],
            'body': row['body'],
            'status': row['status']
        })
    return render_template('send_queue.html', emails=emails_list)


@app.route('/api/send-emails', methods=['POST'])
@login_required
def send_emails():
    """Send emails via real SMTP. Respects test_mode."""
    data = request.get_json(silent=True) or {}
    email_ids = data.get('email_ids', [])
    test_mode = data.get('test_mode', os.environ.get('TEST_MODE', 'true').lower() == 'true')
    if not email_ids:
        return jsonify({'success': False, 'error': 'No emails selected'}), 400

    gmail_user = os.environ.get('GMAIL_USER', '')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')

    if not test_mode and (not gmail_user or not gmail_password):
        return jsonify({
            'success': False,
            'error': 'Gmail credentials not configured in .env. Set GMAIL_USER and GMAIL_APP_PASSWORD.'
        }), 400

    conn = get_db()
    cursor = conn.cursor()
    results = []

    smtp_conn = None
    if not test_mode:
        try:
            smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_conn.starttls()
            smtp_conn.login(gmail_user, gmail_password)
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'error': f'SMTP connection failed: {str(e)}'}), 500

    for email_id in email_ids:
        cursor.execute("""
            SELECT e.subject, e.body, p.email as professor_email, p.name as professor_name, p.id as prof_id
            FROM emails e
            JOIN professors p ON e.professor_id = p.id
            WHERE e.id = ?
        """, (email_id,))
        row = cursor.fetchone()
        if not row:
            results.append({'id': email_id, 'status': 'error', 'message': 'Not found'})
            continue

        if test_mode:
            print(f"[TEST MODE] Would send to {row['professor_name']} <{row['professor_email']}>")
            cursor.execute("UPDATE emails SET status = 'sent' WHERE id = ?", (email_id,))
            results.append({
                'id': email_id,
                'status': 'sent_test',
                'professor': row['professor_name'],
                'email': row['professor_email']
            })
        else:
            try:
                msg = MIMEMultipart()
                msg['From'] = gmail_user
                msg['To'] = row['professor_email']
                msg['Subject'] = row['subject']
                msg.attach(MIMEText(row['body'], 'plain'))
                smtp_conn.send_message(msg)
                cursor.execute("UPDATE emails SET status = 'sent' WHERE id = ?", (email_id,))
                results.append({
                    'id': email_id,
                    'status': 'sent_real',
                    'professor': row['professor_name'],
                    'email': row['professor_email']
                })
            except Exception as e:
                results.append({
                    'id': email_id,
                    'status': 'error',
                    'professor': row['professor_name'],
                    'email': row['professor_email'],
                    'message': str(e)
                })

    if smtp_conn:
        try:
            smtp_conn.quit()
        except:
            pass

    conn.commit()
    conn.close()
    return jsonify({
        'success': True,
        'message': f'Processed {len(results)} emails',
        'results': results,
        'test_mode': test_mode
    })


# ==================== ANALYTICS ====================

@app.route('/analytics')
@login_required
def analytics():
    conn = get_db()
    cursor = conn.cursor()

    def get_count(query):
        cursor.execute(query)
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    total_professors = get_count("SELECT COUNT(*) FROM professors")
    total_emails = get_count("SELECT COUNT(*) FROM emails")
    sent_emails = get_count("SELECT COUNT(*) FROM emails WHERE status = 'sent'")
    ready_emails = get_count("SELECT COUNT(*) FROM emails WHERE status = 'ready'")
    draft_emails = get_count("SELECT COUNT(*) FROM emails WHERE status = 'draft'")
    approved_count = get_count("SELECT COUNT(*) FROM professors WHERE approved = 1")
    rejected_count = get_count("SELECT COUNT(*) FROM professors WHERE approved = 0")
    pending_count = get_count("SELECT COUNT(*) FROM professors WHERE approved IS NULL OR approved NOT IN (0,1)")

    cursor.execute("""
        SELECT p.university, COUNT(e.id) as email_count
        FROM emails e JOIN professors p ON e.professor_id = p.id
        WHERE p.university IS NOT NULL AND p.university != ''
        GROUP BY p.university ORDER BY email_count DESC LIMIT 10
    """)
    university_stats = []
    for row in cursor.fetchall():
        university_stats.append({
            'university': str(row['university']),
            'email_count': int(row['email_count'])
        })

    cursor.execute("""
        SELECT p.department, COUNT(e.id) as email_count
        FROM emails e JOIN professors p ON e.professor_id = p.id
        WHERE p.department IS NOT NULL AND p.department != ''
        GROUP BY p.department ORDER BY email_count DESC LIMIT 10
    """)
    department_stats = []
    for row in cursor.fetchall():
        department_stats.append({
            'department': str(row['department']),
            'email_count': int(row['email_count'])
        })

    cursor.execute("""
        SELECT date(created_at) as day, COUNT(*) as count
        FROM emails WHERE created_at >= date('now', '-30 days')
        GROUP BY date(created_at) ORDER BY day
    """)
    daily_activity = []
    for row in cursor.fetchall():
        daily_activity.append({
            'day': str(row['day']),
            'count': int(row['count'])
        })

    conn.close()
    stats = {
        'total_professors': total_professors,
        'total_emails': total_emails,
        'sent_emails': sent_emails,
        'ready_emails': ready_emails,
        'draft_emails': draft_emails,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'university_stats': university_stats,
        'department_stats': department_stats,
        'daily_activity': daily_activity
    }
    return render_template('analytics.html', stats=stats)


# ==================== SETTINGS ====================

@app.route('/settings')
@login_required
def settings_page():
    config = load_config()
    return render_template('settings.html', config=config)


@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json(silent=True) or {}
    config = load_config()

    allowed_fields = [
        'your_name', 'your_email', 'your_university', 'your_major', 'your_year',
        'research_topic', 'target_universities',
        'emails_per_university', 'max_emails_per_day', 'delay_between_emails',
        'test_mode', 'gmail_user'
    ]
    for field in allowed_fields:
        if field in data:
            config[field] = data[field]

    if save_config(config):
        return jsonify({'success': True, 'message': 'Settings saved'})
    else:
        return jsonify({'success': False, 'error': 'Failed to save settings'}), 500


# ==================== PASSWORD & ACCOUNT ====================

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current = data.get('current_password', '')
    new_pass = data.get('new_password', '')
    confirm = data.get('confirm_password', '')

    if not current or not new_pass:
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    if len(new_pass) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    if new_pass != confirm:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

    user = get_user_by_username(session.get('username', ''))
    if not user or not check_password_hash(user['password_hash'], current):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_pass), user['id'])
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Password updated'})


@app.route('/api/delete-account', methods=['POST'])
@login_required
def delete_account():
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')

    user = get_user_by_username(session.get('username', ''))
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Password is incorrect'}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()

    session.clear()
    return jsonify({'success': True, 'message': 'Account deleted'})


# ==================== BOUNCE DETECTION ====================

@app.route('/bounces')
@login_required
def bounces_page():
    if not BOUNCE_AVAILABLE:
        return render_template('bounces.html', stats=None, error='Bounce detector not available')
    stats = get_bounce_stats()
    return render_template('bounces.html', stats=stats, error=None)


@app.route('/api/check-bounces', methods=['POST'])
@login_required
def api_check_bounces():
    if not BOUNCE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Bounce detector not available'}), 500
    try:
        found = check_bounces()
        return jsonify({
            'success': True,
            'message': f'Checked bounces. Found {len(found)} bounced emails.',
            'bounced_count': len(found),
            'bounced_emails': found
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== EXPORT DATA ====================

@app.route('/api/export/<format>')
@login_required
def export_data(format):
    if format not in ['csv', 'json']:
        return jsonify({'success': False, 'error': 'Format must be csv or json'}), 400

    conn = get_db()
    cursor = conn.cursor()

    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Name', 'University', 'Department', 'Email',
            'Research Interests', 'Approved', 'Created'
        ])
        cursor.execute("""
            SELECT id, name, university, department, email,
                   research_interests, approved, created_at
            FROM professors ORDER BY id DESC
        """)
        for row in cursor.fetchall():
            writer.writerow([
                row['id'], row['name'], row['university'], row['department'],
                row['email'], row['research_interests'], row['approved'], row['created_at']
            ])
        conn.close()
        return (
            output.getvalue(),
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=professors.csv'
            }
        )

    else:  # json
        cursor.execute("SELECT * FROM professors ORDER BY id DESC")
        professors = [dict(row) for row in cursor.fetchall()]
        cursor.execute("""
            SELECT e.*, p.name as professor_name
            FROM emails e
            LEFT JOIN professors p ON e.professor_id = p.id
            ORDER BY e.created_at DESC
        """)
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            'professors': professors,
            'emails': emails,
            'exported_at': datetime.now().isoformat()
        })


# ==================== EMAIL TEMPLATES ====================

@app.route('/api/templates', methods=['GET', 'POST'])
@login_required
def email_templates():
    templates_file = 'email_templates.json'
    if request.method == 'GET':
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'templates': []})

    data = request.get_json(silent=True) or {}
    templates = {'templates': data.get('templates', [])}
    with open(templates_file, 'w') as f:
        json.dump(templates, f, indent=2)
    return jsonify({'success': True, 'message': 'Templates saved'})


# ==================== BULK ACTIONS ====================

@app.route('/api/bulk-approve', methods=['POST'])
@login_required
def bulk_approve():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE professors SET approved = 1 WHERE id = ?",
        [(i,) for i in ids]
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Approved {len(ids)} professors'})


@app.route('/api/bulk-reject', methods=['POST'])
@login_required
def bulk_reject():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE professors SET approved = 0 WHERE id = ?",
        [(i,) for i in ids]
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Rejected {len(ids)} professors'})


# ==================== ADVANCED SEARCH ====================

@app.route('/api/search')
@login_required
def advanced_search():
    query = request.args.get('q', '').strip().lower()
    status = request.args.get('status', '')
    university = request.args.get('university', '')

    conn = get_db()
    cursor = conn.cursor()
    sql = "SELECT * FROM professors WHERE 1=1"
    params = []

    if query:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(university) LIKE ? OR LOWER(department) LIKE ? OR LOWER(email) LIKE ?)"
        params.extend([f'%{query}%'] * 4)
    if status:
        if status == 'approved':
            sql += " AND approved = 1"
        elif status == 'rejected':
            sql += " AND approved = 0"
        elif status == 'pending':
            sql += " AND approved IS NULL"
    if university:
        sql += " AND LOWER(university) LIKE ?"
        params.append(f'%{university.lower()}%')

    sql += " ORDER BY id DESC"
    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'results': results, 'count': len(results)})


# ==================== EMAIL SCHEDULING ====================

@app.route('/api/schedule-email', methods=['POST'])
@login_required
def schedule_email():
    data = request.get_json(silent=True) or {}
    email_id = data.get('email_id')
    send_at = data.get('send_at')

    if not email_id or not send_at:
        return jsonify({'success': False, 'error': 'email_id and send_at required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scheduled_emails (email_id, send_at)
        VALUES (?, ?)
    """, (email_id, send_at))

    cursor.execute("UPDATE emails SET status = 'scheduled' WHERE id = ?", (email_id,))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Email scheduled for {send_at}'})


@app.route('/scheduled')
@login_required
def scheduled_emails_page():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, e.subject, p.name as professor_name, p.email as professor_email, p.university
        FROM scheduled_emails s
        JOIN emails e ON s.email_id = e.id
        JOIN professors p ON e.professor_id = p.id
        WHERE s.status = 'scheduled'
        ORDER BY s.send_at ASC
    """)
    scheduled = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('scheduled.html', scheduled=scheduled)


# ==================== FAVICON ====================

@app.route('/favicon.ico')
def favicon():
    return '', 204


# ==================== FULL PIPELINE ====================

@app.route('/api/run-pipeline', methods=['POST'])
@login_required
def api_run_pipeline():
    """Run full pipeline: Discover -> Find Emails -> Generate -> Send (test mode)"""
    results = {'steps': [], 'success': True}

    if DISCOVERY_AVAILABLE:
        try:
            config = load_config()
            discover_all_professors(
                config.get('target_universities', ['MIT']),
                config.get('research_topic', 'Research'),
                config.get('emails_per_university', 5)
            )
            results['steps'].append({'step': 1, 'name': 'Discover Professors', 'status': 'done'})
        except Exception as e:
            results['steps'].append({'step': 1, 'name': 'Discover Professors', 'status': 'error', 'error': str(e)})
            results['success'] = False
    else:
        results['steps'].append({'step': 1, 'name': 'Discover Professors', 'status': 'skipped'})

    if EMAIL_FINDER_AVAILABLE:
        try:
            run_email_finder()
            results['steps'].append({'step': 2, 'name': 'Find Emails', 'status': 'done'})
        except Exception as e:
            results['steps'].append({'step': 2, 'name': 'Find Emails', 'status': 'error', 'error': str(e)})
            results['success'] = False
    else:
        results['steps'].append({'step': 2, 'name': 'Find Emails', 'status': 'skipped'})

    if PERSONALIZATION_AVAILABLE:
        try:
            run_personalization()
            results['steps'].append({'step': 3, 'name': 'Generate Emails', 'status': 'done'})
        except Exception as e:
            results['steps'].append({'step': 3, 'name': 'Generate Emails', 'status': 'error', 'error': str(e)})
            results['success'] = False
    else:
        results['steps'].append({'step': 3, 'name': 'Generate Emails', 'status': 'skipped'})

    if SENDER_AVAILABLE:
        try:
            run_sender()
            results['steps'].append({'step': 4, 'name': 'Send Emails', 'status': 'done'})
        except Exception as e:
            results['steps'].append({'step': 4, 'name': 'Send Emails', 'status': 'error', 'error': str(e)})
            results['success'] = False
    else:
        results['steps'].append({'step': 4, 'name': 'Send Emails', 'status': 'skipped'})

    return jsonify(results)


# ==================== DASHBOARD API ENDPOINTS ====================

@app.route('/api/discover', methods=['POST'])
@login_required
def api_discover():
    if not DISCOVERY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Discovery module not available. Check console.'}), 500
    try:
        config = load_config()
        discover_all_professors(
            config.get('target_universities', ['MIT']),
            config.get('research_topic', 'Research'),
            config.get('emails_per_university', 5)
        )
        return jsonify({'success': True, 'message': 'Professors discovered and saved to database'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/find-emails', methods=['POST'])
@login_required
def api_find_emails():
    if not EMAIL_FINDER_AVAILABLE:
        return jsonify({'success': False, 'error': 'Email finder module not available'}), 500
    try:
        run_email_finder()
        return jsonify({'success': True, 'message': 'Emails found and saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    if not PERSONALIZATION_AVAILABLE:
        return jsonify({'success': False, 'error': 'Personalization module not available'}), 500
    try:
        run_personalization()
        return jsonify({'success': True, 'message': 'Emails generated with AI'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/send', methods=['POST'])
@login_required
def api_send():
    if not SENDER_AVAILABLE:
        return jsonify({'success': False, 'error': 'Sender module not available'}), 500
    try:
        run_sender()
        return jsonify({'success': True, 'message': 'Emails sent'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
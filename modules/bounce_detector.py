"""Bounce detector using IMAP to scan inbox for delivery failures."""
import imaplib
import email
from email.header import decode_header
import os
import re
import socket

# Common bounce-related subjects and patterns
BOUNCE_PATTERNS = [
    r'mail delivery failed',
    r'delivery status notification',
    r'delivery failure',
    r'undelivered mail',
    r'message not delivered',
    r'bounce',
    r'returned mail',
    r'daemon',
    r'mailer-daemon',
]

BOUNCE_SENDERS = [
    'mailer-daemon',
    'postmaster',
    'mail delivery subsystem',
    'daemon',
]


def _get_imap_config():
    """Load IMAP credentials from environment."""
    return {
        'user': os.environ.get('GMAIL_USER', ''),
        'password': os.environ.get('GMAIL_APP_PASSWORD', ''),
        'host': 'imap.gmail.com',
        'port': 993,
    }


def _is_bounce(msg):
    """Check if a message is a bounce based on subject and sender."""
    subject = ''
    sender = ''

    # Decode subject
    raw_subject = msg.get('Subject', '')
    if raw_subject:
        decoded = decode_header(raw_subject)
        subject_parts = []
        for part, charset in decoded:
            if isinstance(part, bytes):
                try:
                    subject_parts.append(part.decode(charset or 'utf-8', errors='replace'))
                except:
                    subject_parts.append(part.decode('utf-8', errors='replace'))
            else:
                subject_parts.append(part)
        subject = ' '.join(subject_parts).lower()

    # Decode sender
    raw_from = msg.get('From', '')
    if raw_from:
        decoded = decode_header(raw_from)
        sender_parts = []
        for part, charset in decoded:
            if isinstance(part, bytes):
                try:
                    sender_parts.append(part.decode(charset or 'utf-8', errors='replace'))
                except:
                    sender_parts.append(part.decode('utf-8', errors='replace'))
            else:
                sender_parts.append(part)
        sender = ' '.join(sender_parts).lower()

    # Check subject patterns
    for pattern in BOUNCE_PATTERNS:
        if pattern in subject:
            return True

    # Check sender patterns
    for bounce_sender in BOUNCE_SENDERS:
        if bounce_sender in sender:
            return True

    return False


def _extract_bounced_email(msg):
    """Try to extract the original recipient email from bounce message body."""
    bounced = []
    # Check all parts of the message
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain' or content_type == 'text/html':
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        text = body.decode('utf-8', errors='replace')
                        # Look for email patterns in bounce body
                        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                        found = re.findall(email_pattern, text)
                        bounced.extend(found)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True)
            if body:
                text = body.decode('utf-8', errors='replace')
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found = re.findall(email_pattern, text)
                bounced.extend(found)
        except:
            pass

    # Also check X-Failed-Recipients header
    failed = msg.get('X-Failed-Recipients', '')
    if failed:
        bounced.append(failed)

    return list(set(bounced)) if bounced else []


def check_bounces():
    """Check Gmail inbox for bounce messages via IMAP."""
    config = _get_imap_config()

    if not config['user'] or not config['password']:
        print("[Bounce Detector] IMAP credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        return []

    bounced_emails = []
    mail = None
    try:
        # Set socket timeout to prevent hanging forever
        socket.setdefaulttimeout(10)

        mail = imaplib.IMAP4_SSL(config['host'], config['port'])
        mail.login(config['user'], config['password'])
        mail.select('inbox')

        # Search for unread messages
        _, search_data = mail.search(None, 'UNSEEN')
        message_ids = search_data[0].split()

        if not message_ids:
            # If no unread, check last 50 messages
            _, search_data = mail.search(None, 'ALL')
            all_ids = search_data[0].split()
            message_ids = all_ids[-50:] if len(all_ids) > 50 else all_ids

        for msg_id in message_ids:
            _, msg_data = mail.fetch(msg_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if _is_bounce(msg):
                        bounced = _extract_bounced_email(msg)
                        bounced_emails.extend(bounced)

        mail.logout()
        print(f"[Bounce Detector] Checked inbox. Found {len(bounced_emails)} bounced email addresses.")
        return list(set(bounced_emails))

    except socket.timeout:
        print("[Bounce Detector] IMAP connection timed out. Check your internet or Gmail IMAP settings.")
        return []
    except Exception as e:
        print(f"[Bounce Detector] IMAP error: {e}")
        return []
    finally:
        # Reset socket timeout
        socket.setdefaulttimeout(None)
        if mail:
            try:
                mail.close()
            except:
                pass
            try:
                mail.logout()
            except:
                pass


def get_bounce_stats():
    """Get bounce statistics."""
    bounced = check_bounces()
    return {
        'total_checked': 50,  # Approximate - last 50 messages checked
        'bounced_count': len(bounced),
        'bounced_emails': bounced
    }
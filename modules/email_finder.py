"""Find email addresses for professors using pattern guessing and MX validation."""
import sqlite3
import dns.resolver

DB_PATH = 'professor_outreach.db'


def _get_domain(university):
    """Map university name to email domain."""
    domain_map = {
        'mit': 'mit.edu',
        'massachusetts institute of technology': 'mit.edu',
        'stanford': 'stanford.edu',
        'cmu': 'cmu.edu',
        'carnegie mellon': 'cmu.edu',
        'berkeley': 'berkeley.edu',
        'uc berkeley': 'berkeley.edu',
        'harvard': 'harvard.edu',
        'university of toronto': 'utoronto.ca',
        'toronto': 'utoronto.ca',
        'vit university': 'vit.ac.in',
        'vit': 'vit.ac.in',
        'indian institute of technology kharagpur': 'iitkgp.ac.in',
        'iit kharagpur': 'iitkgp.ac.in',
        'jadavpur university': 'jadavpuruniversity.in',
        'jadavpur': 'jadavpuruniversity.in',
    }
    uni_lower = university.lower()
    for key, domain in domain_map.items():
        if key in uni_lower:
            return domain
    # Fallback: clean university name
    clean = university.lower().replace(' ', '').replace(',', '')
    return f"{clean}.edu"


def _generate_patterns(first_name, last_name, domain):
    """Generate common academic email patterns."""
    f = first_name.lower().strip()
    l = last_name.lower().strip()
    fi = f[0] if f else ''
    li = l[0] if l else ''

    patterns = [
        f"{f}.{l}@{domain}",
        f"{fi}{l}@{domain}",
        f"{f}{l}@{domain}",
        f"{f}_{l}@{domain}",
        f"{f}-{l}@{domain}",
        f"{l}.{f}@{domain}",
        f"{fi}.{l}@{domain}",
        f"{f}{li}@{domain}",
        f"{l}@{domain}",
        f"{f}@{domain}",
    ]
    return list(dict.fromkeys(patterns))  # Remove duplicates while preserving order


def _validate_mx(domain):
    """Check if domain has valid MX records using dnspython."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception:
        return False


def _validate_email_pattern(email, domain):
    """Validate that the email domain has MX records."""
    return _validate_mx(domain)


def run():
    """Find email addresses for professors missing them using pattern guessing."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, university FROM professors WHERE email IS NULL OR email = ''")
    rows = cursor.fetchall()

    updated = 0
    for row in rows:
        name = row['name']
        university = row['university']

        # Parse name into first and last
        parts = name.strip().split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[-1]
        elif len(parts) == 1:
            first_name = parts[0]
            last_name = parts[0]
        else:
            first_name = 'prof'
            last_name = str(row['id'])

        domain = _get_domain(university)

        # Validate domain has MX records
        if not _validate_mx(domain):
            print(f"[Email Finder] Warning: No MX records for {domain} ({university})")
            # Still generate pattern but flag it

        patterns = _generate_patterns(first_name, last_name, domain)
        best_guess = patterns[0] if patterns else f"{first_name.lower()}.{last_name.lower()}@{domain}"

        cursor.execute("UPDATE professors SET email = ? WHERE id = ?", (best_guess, row['id']))
        updated += 1

        if updated <= 3:
            print(f"[Email Finder] {name} -> {best_guess} (domain: {domain}, MX valid: {_validate_mx(domain)})")

    conn.commit()
    conn.close()
    print(f"[Email Finder] Updated {updated} professors with pattern-guessed emails")
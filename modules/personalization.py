"""Personalized email generation - human-like, varied, professor-specific."""
import json
import os
import random
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
DB_PATH = str(_PROJECT_ROOT / "professor_outreach.db")
CONFIG_PATH = _PROJECT_ROOT / "config.json"

# Try to import OpenAI, fallback to template if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] OpenAI not installed. Run: pip install openai")


def _read_openai_key_from_env_file() -> str:
    """Read OPENAI_API_KEY from .env when dotenv misses a split/wrapped value."""
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return ""
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("OPENAI_API_KEY="):
            value = stripped.split("=", 1)[1].strip()
            if value:
                return value
            if i + 1 < len(lines):
                return lines[i + 1].strip()
    return ""


def _load_config():
    """Load config from config.json - unified with app.py."""
    defaults = {
        "your_name": "User",
        "your_email": "user@example.com",
        "your_university": "Your Institution",
        "research_topic": "Research",
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    except (OSError, json.JSONDecodeError):
        pass
    return defaults


def generate_email_with_ai(name, university, department, research_interests,
                           your_name, your_institution, your_email, research_topic):
    """Generate a truly unique email using OpenAI API."""
    if not OPENAI_AVAILABLE:
        return None

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        api_key = _read_openai_key_from_env_file()
    if not api_key:
        print("[WARN] OPENAI_API_KEY not set. Add it to your .env file on one line.")
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""Write a personalized cold email from a student to a professor for research collaboration.

Professor: {name}
University: {university}
Department: {department}
Their research: {research_interests}

Student: {your_name}
Student's institution: {your_institution}
Student's research interest: {research_topic}
Student's email: {your_email}

Write a warm, natural, human-like email (250-350 words) that:
1. Opens with a specific, genuine observation about their work (not generic praise)
2. Shows you actually read their papers by referencing a specific technique, paper title, or research direction
3. Explains YOUR background briefly but naturally - mention what sparked your interest
4. Connects your work to theirs in a specific, non-obvious way
5. Asks for advice or a brief chat (not a formal meeting)
6. Uses varied sentence structure - mix short and long sentences
7. Includes one personal touch - a brief anecdote or genuine curiosity
8. Sounds like a real human wrote it, not AI. Use conversational but professional tone.
9. Vary the opening - don't always start with "I hope this email finds you well"
10. End with something warm but not overly formal

Return ONLY the email body text, no subject line, no extra text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.85
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Error] {e}")
        return None


# Collection of human-like openings - varied and natural (using triple quotes for multi-line)
_OPENINGS = [
    """Dear Professor {name},

I came across your recent work on {interests} while researching potential advisors for graduate study, and I was struck by how your approach to {specific} differs from the conventional methods I've seen in the literature.""",

    """Dear Professor {name},

My advisor, {advisor_mention}, actually mentioned your paper on {interests} during a seminar last month, and I've been thinking about it ever since. The way you {specific} really resonated with some challenges I've been facing in my own work.""",

    """Dear Professor {name},

I've been following the {dept} at {university} for a while now — your group's work on {interests} keeps coming up in my literature reviews, and I finally decided I should reach out directly.""",

    """Dear Professor {name},

I'll be honest — I wasn't planning to email anyone this week, but I just read your paper on {interests} and couldn't shake the feeling that our research paths might intersect in interesting ways.""",

    """Dear Professor {name},

A colleague of mine at {your_institution} pointed me toward your research on {interests} last semester, and after spending the past few months diving deeper into your publications, I wanted to introduce myself and share why your work matters to me.""",

    """Dear Professor {name},

I found myself on your lab's website at 2 AM last Tuesday (the kind of night that only PhD students understand), and your project on {interests} made me pause my caffeine-fueled scrolling session.""",

    """Dear Professor {name},

During a recent conference on {research_topic}, I kept hearing your name come up in conversations about {interests}. Rather than rely on secondhand impressions, I thought I'd reach out directly to learn more about your perspective.""",
]

# Collection of body paragraphs - varied based on department and research
_BODY_TEMPLATES = {
    "cs_ml": [
        """My background is in {research_topic}, and I've been particularly focused on {specific}. What drew me to your work was your recent exploration of {interests} — specifically, the way you handle {detail}. In my own research, I've been grappling with similar challenges around {challenge}, and I keep wondering whether techniques from your domain might offer a fresh angle.""",

        """I've spent the past two years working on {research_topic} at {your_institution}, where I've developed a particular interest in {specific}. Your group's approach to {interests} caught my attention because it seems to address a gap I've noticed in the current literature — namely, {detail}. I'd love to hear your thoughts on whether {challenge} might benefit from cross-pollination with your methods.""",
    ],
    "cs_vision": [
        """As someone who's been working on {research_topic} for the past year, I found your recent contributions to {interests} particularly compelling. The visual representations your team generates for {detail} seem like they could inform some of the interpretability challenges I'm facing in my own project on {challenge}.""",

        """My research in {research_topic} has increasingly led me toward questions about visual understanding and perception. Your lab's work on {interests} represents exactly the kind of rigorous empirical foundation I think my theoretical framework needs — especially your findings around {detail}.""",
    ],
    "cs_nlp": [
        """I've been working on {research_topic} with a focus on {specific}, and your group's publications on {interests} have become essential reading for me. The linguistic patterns you identify in {detail} seem directly relevant to some anomalies I've been observing in my own data around {challenge}.""",

        """Language and computation have been my primary interests since undergrad, and your work on {interests} at {university} represents some of the most thoughtful scholarship I've encountered in this space. I'm especially curious about your perspective on {detail} and whether you see connections to {challenge}.""",
    ],
    "cs_systems": [
        """My work on {research_topic} has given me a deep appreciation for systems-level thinking, which is why your research on {interests} resonated with me. The scalability challenges you address in {detail} mirror some of the bottlenecks I've been wrestling with in my own project on {challenge}.""",

        """At {your_institution}, I've been building systems for {research_topic}, and I keep running into fundamental questions about {challenge}. Your group's work on {interests} seems to offer a principled way of thinking about these issues — particularly your approach to {detail}.""",
    ],
    "bio": [
        """My research in {research_topic} has increasingly required me to think across disciplinary boundaries, which is how I found my way to your work on {interests}. The biological mechanisms you study in {detail} seem to offer a compelling analogy for some computational processes I've been modeling.""",

        """I've been fascinated by the intersection of {research_topic} and biological systems since my undergraduate days. Your research on {interests} at {university} represents precisely the kind of interdisciplinary bridge I've been hoping to build in my own career.""",
    ],
    "default": [
        """My research focuses on {research_topic}, specifically {specific}. I've been following your work on {interests} for some time now, and I'm particularly intrigued by your approach to {detail}. It seems like there might be an interesting conversation to be had about how {challenge} could benefit from insights in your domain.""",

        """At {your_institution}, I've been developing expertise in {research_topic} with an emphasis on {specific}. Your publications on {interests} have shaped how I think about {challenge}, and I'd value the opportunity to learn from your perspective on {detail}.""",
    ]
}

# Collection of closing paragraphs - warm but professional
_CLOSINGS = [
    """I know your time is precious, so I'll keep this brief. I'd love to hear your thoughts on whether there might be room for a brief conversation — even 15 minutes over Zoom would mean a great deal to me. No pressure at all if you're swamped; I completely understand.""",

    """I'm not looking for a commitment or a formal collaboration right now — honestly, I'd just value your perspective on where my research might fit into the broader landscape. If you have 10 minutes for a virtual coffee chat in the coming weeks, I'd be grateful.""",

    """If this email finds you at a busy time, please don't feel any obligation to respond. But if you happen to have a moment to share your thoughts — even just a sentence or two about whether this direction seems worth pursuing — it would mean more than you know.""",

    """I should mention that I'll actually be attending the upcoming conference on {research_topic} in a few months — if you plan to be there, I'd love to buy you a coffee and hear about your latest work in person. If not, a brief email exchange would still be wonderful.""",

    """Your work has already influenced how I approach my research, and I'd be honored to learn from you directly. Even a brief pointer to a paper or resource I might have missed would be incredibly valuable. Thank you for reading this far.""",
]

# Collection of sign-offs - varied and warm (triple-quoted for multi-line strings)
_SIGN_OFFS = [
    """Warmly,
{your_name}
{your_institution}
{your_email}""",
    """Best,
{your_name}
{your_institution}
{your_email}""",
    """With gratitude,
{your_name}
{your_institution}
{your_email}""",
    """Thanks so much for your time,
{your_name}
{your_institution}
{your_email}""",
    """Looking forward to hearing from you,
{your_name}
{your_institution}
{your_email}""",
]


def _pick_template_category(department, research_interests):
    """Pick the most relevant template category based on department and interests."""
    dept_lower = (department or '').lower()
    interests_lower = (research_interests or '').lower()

    if any(k in dept_lower or k in interests_lower for k in ['vision', 'image', 'cv', 'perception']):
        return 'cs_vision'
    if any(k in dept_lower or k in interests_lower for k in ['nlp', 'language', 'text', 'linguistic', 'speech']):
        return 'cs_nlp'
    if any(k in dept_lower or k in interests_lower for k in ['system', 'distributed', 'cloud', 'database', 'network']):
        return 'cs_systems'
    if any(k in dept_lower or k in interests_lower for k in ['bio', 'life', 'medical', 'health', 'genomic']):
        return 'bio'
    if any(k in dept_lower or k in interests_lower for k in ['ml', 'learning', 'ai', 'intelligence', 'neural', 'deep']):
        return 'cs_ml'
    return 'default'


def _generate_specific_detail(interests):
    """Generate a specific, plausible detail from research interests."""
    if not interests:
        return "the methodological framework"

    terms = [t.strip() for t in interests.split(',')]
    if len(terms) >= 2:
        return f"the relationship between {terms[0]} and {terms[1]}"
    elif terms:
        return f"{terms[0]} in real-world applications"
    return "the methodological framework"


def _generate_challenge(research_topic):
    """Generate a plausible challenge based on research topic."""
    challenges = [
        f"scaling {research_topic} methods to larger datasets",
        f"interpreting the results of {research_topic} models",
        f"bridging the gap between theory and practice in {research_topic}",
        f"handling edge cases in {research_topic} applications",
        f"making {research_topic} accessible to non-experts",
        f"ensuring robustness in {research_topic} systems",
        f"reducing computational costs in {research_topic}",
    ]
    return random.choice(challenges)


def _generate_advisor_mention():
    """Generate a plausible advisor/colleague mention."""
    names = ["Dr. Chen", "Dr. Rodriguez", "Dr. Patel", "Dr. Kim", "Dr. Thompson",
             "my research mentor", "a visiting professor", "a colleague"]
    return random.choice(names)


def generate_email_content(name, university, department, research_interests,
                           your_name, your_institution, your_email, research_topic):
    """Generate a human-like, personalized email. Try AI first, fallback to smart template."""

    # Attempt AI generation first
    ai_email = generate_email_with_ai(
        name, university, department, research_interests,
        your_name, your_institution, your_email, research_topic
    )

    if ai_email:
        return ai_email

    # Fallback: smart template with high variation
    interests = research_interests or 'your research area'
    dept = department or 'your department'

    # Pick random components
    opening_template = random.choice(_OPENINGS)
    category = _pick_template_category(department, research_interests)
    body_template = random.choice(_BODY_TEMPLATES.get(category, _BODY_TEMPLATES['default']))
    closing_template = random.choice(_CLOSINGS)
    sign_off = random.choice(_SIGN_OFFS)

    # Generate specific details
    specific = _generate_specific_detail(research_interests)
    challenge = _generate_challenge(research_topic)
    advisor = _generate_advisor_mention()

    # Build the opening
    opening = opening_template.format(
        name=name,
        university=university,
        dept=dept,
        interests=interests,
        specific=specific,
        your_institution=your_institution,
        advisor_mention=advisor,
        research_topic=research_topic
    )

    # Build the body
    body = body_template.format(
        name=name,
        university=university,
        dept=dept,
        interests=interests,
        specific=specific,
        detail=specific,
        challenge=challenge,
        research_topic=research_topic,
        your_name=your_name,
        your_institution=your_institution
    )

    # Build the closing
    closing = closing_template.format(
        research_topic=research_topic,
        your_name=your_name
    )

    # Build sign-off
    sign_off = sign_off.format(
        your_name=your_name,
        your_institution=your_institution,
        your_email=your_email
    )

    # Assemble full email with natural paragraph breaks
    return "\n\n".join([opening, body, closing, sign_off])


def run():
    """Generate emails for professors with emails but no generated email yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    config = _load_config()

    your_name = config.get('your_name', 'User')
    your_email = config.get('your_email', 'user@example.com')
    your_institution = config.get('your_university', 'Your Institution')
    research_topic = config.get('research_topic', 'Research')

    cursor.execute("""
        SELECT p.id, p.name, p.university, p.department, p.email, p.research_interests
        FROM professors p
        WHERE p.email IS NOT NULL AND p.email != ''
        AND p.id NOT IN (SELECT professor_id FROM emails)
    """)

    rows = cursor.fetchall()
    added = 0
    for row in rows:
        subject = f"Research inquiry: {research_topic} and {row['research_interests'] or 'your work'}"

        body = generate_email_content(
            row['name'], row['university'], row['department'], row['research_interests'],
            your_name, your_institution, your_email, research_topic
        )

        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO emails (professor_id, subject, body, status, created_at, updated_at)
            VALUES (?, ?, ?, 'draft', ?, ?)
            """,
            (row["id"], subject, body, now, now),
        )
        added += 1

        # Print preview of first email
        if added == 1:
            print(f"\n[Preview] First email for {row['name']}:")
            print("-" * 50)
            print(body[:500] + "..." if len(body) > 500 else body)
            print("-" * 50 + "\n")

    conn.commit()
    conn.close()
    print(f"[Personalization] Generated {added} personalized emails")
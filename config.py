"""Config module that reads config.json for backward compatibility."""
import json
import os


def _load_config():
    """Load config from config.json."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "target_universities": ["MIT", "Stanford"],
            "research_topic": "Machine Learning",
            "emails_per_university": 5
        }


_config = _load_config()

# Export variables for backward compatibility with any code that does:
# from config import TARGET_UNIVERSITIES, RESEARCH_TOPIC, EMAILS_PER_UNIVERSITY
TARGET_UNIVERSITIES = _config.get('target_universities', ['MIT', 'Stanford'])
RESEARCH_TOPIC = _config.get('research_topic', 'Machine Learning')
EMAILS_PER_UNIVERSITY = _config.get('emails_per_university', 5)
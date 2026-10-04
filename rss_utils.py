import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def sanitize_xml_text(text: str) -> str:
    """Ensures all ampersands and special XML characters are safely escaped."""
    if not text:
        return ""
    # First unescape to avoid double escaping &amp;amp;
    unescaped = html.unescape(text)
    # Then escape properly for XML
    return html.escape(unescaped)

def validate_and_save_rss(rss_file_path: Path, new_content: str) -> bool:
    """
    Parses new_content with ElementTree to guarantee 100% valid XML
    BEFORE writing to disk. Returns True if valid, raises error if invalid.
    """
    try:
        ET.fromstring(new_content)
        rss_file_path.write_text(new_content, encoding="utf-8")
        print("[RSS VALIDATION SUCCESS] rss.xml passed full ElementTree XML parse check!", flush=True)
        return True
    except ET.ParseError as e:
        print(f"[RSS VALIDATION WARNING] XML Parse Error detected: {e}. Repairing unescaped ampersands...", flush=True)
        repaired = re.sub(r'&(?!(amp|lt|gt|apos|quot);)', '&amp;', new_content)
        try:
            ET.fromstring(repaired)
            rss_file_path.write_text(repaired, encoding="utf-8")
            print("[RSS VALIDATION SUCCESS] Repaired and validated rss.xml!", flush=True)
            return True
        except ET.ParseError as e2:
            print(f"[RSS FATAL ERROR] Could not repair XML: {e2}", flush=True)
            raise e2

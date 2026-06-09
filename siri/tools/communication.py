"""Communication tools: Gmail and WhatsApp via browser automation."""

from __future__ import annotations

from siri.tools import browser as browser_tools

_composed_email: dict | None = None


def _ok(result) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def compose_email(to: str, subject: str, body: str) -> dict:
    global _composed_email
    _composed_email = {"to": to, "subject": subject, "body": body}
    result = browser_tools.browser_open("https://mail.google.com/mail/u/0/#inbox?compose=new")
    if not result["success"]:
        return result
    return _ok("Email composed in Gmail — review and say send when ready")


def send_email() -> dict:
    global _composed_email
    if not _composed_email:
        return _err("No email composed. Use compose_email first.")
    browser_tools.browser_fill_form('input[name="to"]', _composed_email["to"])
    browser_tools.browser_fill_form('input[name="subjectbox"]', _composed_email["subject"])
    browser_tools.browser_fill_form('div[aria-label="Message Body"]', _composed_email["body"])
    browser_tools.browser_click_element('div[role="button"]:has-text("Send")')
    _composed_email = None
    return _ok("Email sent")


def read_latest_emails(count: int = 5) -> dict:
    result = browser_tools.browser_open("https://mail.google.com")
    if not result["success"]:
        return result
    text = browser_tools.browser_get_text()
    return _ok(text.get("result", "")[:2000] if text["success"] else "Could not read emails")


def send_whatsapp(contact: str, message: str) -> dict:
    import urllib.parse

    encoded = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={contact}&text={encoded}"
    result = browser_tools.browser_open(url)
    if not result["success"]:
        return result
    browser_tools.browser_click_element('span[data-icon="send"]')
    return _ok(f"Message sent to {contact}")

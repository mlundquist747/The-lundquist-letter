#!/usr/bin/env python3
"""
The Lundquist Letter — Morning Briefing Sender
Generates a personalized newspaper-style briefing and sends it via Gmail.
"""

import os
import json
import base64
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── CONFIG ──────────────────────────────────────────────────────────────────

RECIPIENT_EMAIL = "mlundquist747@gmail.com"
SENDER_EMAIL    = "mlundquist747@gmail.com"

PREFS = {
    "topics":   ["Manufacturing","Finance","Investing","Software/Tech","Business",
                 "Economics","Football","Baseball","Hockey","Health","Medicine","Research"],
    "categories": ["Politics","Business & Finance","Technology","Science & Health",
                   "World News","Local News"],
    "excludes": ["celebrity gossip","culture","minor political stories","entertainment"],
    "sources":  ["WSJ","NYT","The Economist","Reuters","AP News","TechCrunch","ESPN"],
    "blocked":  ["NY Post","The Guardian","TMZ"],
    "teams":    ["Texas A&M","Houston Texans","Houston Astros"],
    "leagues":  ["NFL","MLB","NHL","College Football","College Basketball","Golf"],
    "location": "Cypress, Texas",
}

# ── ANTHROPIC CLIENT ─────────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def call_claude(system: str, user: str, max_tokens: int = 2500) -> str:
    """Call Claude with web search enabled and return text response."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def parse_json(raw: str):
    """Strip markdown fences and parse first JSON array or object found."""
    clean = re.sub(r"```json\s*|```", "", raw).strip()
    for pattern in (r"\[.*\]", r"\{.*\}"):
        m = re.search(pattern, clean, re.DOTALL)
        if m:
            return json.loads(m.group())
    raise ValueError("No JSON found in response")


# ── DATA FETCHERS ────────────────────────────────────────────────────────────

def fetch_quote(today: str) -> dict:
    raw = call_claude(
        "Return ONLY valid JSON: {\"quote\":\"...\",\"author\":\"...\"}. No markdown.",
        f"One timeless, meditative morning quote for {today}. Topics: {', '.join(PREFS['topics'])}.",
        300,
    )
    try:
        return parse_json(raw)
    except Exception:
        return {"quote": "The secret of getting ahead is getting started.", "author": "Mark Twain"}


def fetch_markets(today: str) -> list:
    raw = call_claude(
        "Return ONLY a valid JSON array. Each item: {\"symbol\":\"...\",\"price\":\"...\",\"change\":\"...\",\"direction\":\"up|down|flat\"}. No markdown.",
        f"Today is {today}. Current prices for: S&P 500, Dow Jones, NASDAQ, 10-yr Treasury yield, WTI Crude Oil, Gold.",
        600,
    )
    try:
        return parse_json(raw)
    except Exception:
        return []


def fetch_news(today: str) -> list:
    sys_prompt = f"""You are a world-class newspaper editor curating a personalized morning briefing.
Topics of interest: {', '.join(PREFS['topics'])}.
Categories: {', '.join(PREFS['categories'])}.
Exclude: {', '.join(PREFS['excludes'])}.
Preferred sources: {', '.join(PREFS['sources'])}.
Blocked sources: {', '.join(PREFS['blocked'])}.
Return ONLY a valid JSON array. Each object:
{{"eyebrow":"CATEGORY","headline":"...","source":"...","byline":"","digest":"2-3 sentence summary","url":"real article URL","tier":1|2|3}}
Tier 1 = top 2 most important stories. Tier 2 = business/tech/science (3 stories). Tier 3 = world/health/policy (4-6 stories).
Total: 9-11 articles. Every article MUST have a real working URL."""
    raw = call_claude(
        sys_prompt,
        f"Today is {today}. Search for the most important news right now across all my interest areas. Return 9-11 articles as JSON.",
        3500,
    )
    return parse_json(raw)


def fetch_sports(today: str) -> dict:
    sys_prompt = f"""You are a sports editor. User follows: {', '.join(PREFS['leagues'])}. Favorite teams: {', '.join(PREFS['teams'])}.
Return ONLY a valid JSON object with two keys:
"scores": [{{"league":"NFL","home":"Team A","homeScore":"21","away":"Team B","awayScore":"14","status":"Final","winner":"home|away|none"}}]
"stories": [{{"eyebrow":"NFL","headline":"...","source":"...","digest":"2-3 sentences","url":"real URL"}}]
5-8 scores, 3-4 stories. Prioritize Houston Texans, Houston Astros, Texas A&M. No markdown."""
    raw = call_claude(
        sys_prompt,
        f"Today is {today}. Latest scores and top sports news for NFL, MLB, NHL, College Football, College Basketball, Golf. Focus on Texans, Astros, Texas A&M.",
        2000,
    )
    return parse_json(raw)


# ── HTML BUILDER ─────────────────────────────────────────────────────────────

def direction_color(d: str) -> str:
    return {"up": "#27ae60", "down": "#c0392b"}.get(d, "#888888")


def article_html(a: dict, headline_size: str = "16px", show_digest: bool = True) -> str:
    eyebrow = f'<div style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#8b1a1a;margin-bottom:4px">{a.get("eyebrow","")}</div>' if a.get("eyebrow") else ""
    byline_parts = [a.get("source","")]
    if a.get("byline"): byline_parts.append(a["byline"])
    byline = f'<div style="font-family:Arial,sans-serif;font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">{" · ".join(byline_parts)}</div>'
    digest = f'<p style="font-size:13px;line-height:1.7;color:#444;margin:0 0 6px">{a.get("digest","")}</p>' if show_digest and a.get("digest") else ""
    read_more = f'<a href="{a["url"]}" style="font-family:Arial,sans-serif;font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8b1a1a;text-decoration:none">Read more →</a>' if a.get("url") else ""
    return f"""
    <div style="padding:12px 0;border-top:1px solid #ddd">
      {eyebrow}
      <h3 style="font-family:Georgia,serif;font-size:{headline_size};font-weight:700;line-height:1.2;color:#1a1714;margin:0 0 5px">{a.get("headline","")}</h3>
      {byline}
      {digest}
      {read_more}
    </div>"""


def build_email_html(today: str, quote: dict, markets: list, articles: list, sports: dict) -> str:
    tier1 = [a for a in articles if a.get("tier") == 1][:2]
    tier2 = [a for a in articles if a.get("tier") == 2][:3]
    tier3 = [a for a in articles if a.get("tier") == 3]

    # Markets bar
    tickers_html = ""
    for t in markets:
        color = direction_color(t.get("direction","flat"))
        tickers_html += f'<span style="margin-right:20px;white-space:nowrap"><span style="color:#ccc;font-size:11px">{t.get("symbol","")} </span><span style="color:#fff;font-size:11px">{t.get("price","")} </span><span style="color:{color};font-size:11px">{t.get("change","")}</span></span>'

    # Top stories — 2 column
    top_html = ""
    for i, a in enumerate(tier1):
        border = 'border-left:1px solid #ddd;padding-left:20px' if i == 1 else ''
        top_html += f'<td valign="top" style="width:50%;{border};padding-bottom:0">{article_html(a,"20px",True)}</td>'

    # Mid stories — 3 column
    mid_html = ""
    for i, a in enumerate(tier2):
        border = 'border-left:1px solid #ddd;padding-left:16px' if i > 0 else ''
        mid_html += f'<td valign="top" style="width:33%;{border}">{article_html(a,"15px",True)}</td>'

    # Bottom stories — 2 column
    half = len(tier3) // 2 + len(tier3) % 2
    left_stories  = "".join(article_html(a, "13px", True) for a in tier3[:half])
    right_stories = "".join(article_html(a, "13px", True) for a in tier3[half:])

    # Sports scores
    scores_html = ""
    for s in sports.get("scores", [])[:8]:
        home_w = s.get("winner") == "home"
        away_w = s.get("winner") == "away"
        scores_html += f"""
        <div style="border-top:1px solid #e0e0e0;padding:8px 0">
          <div style="font-family:Arial,sans-serif;font-size:8px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;color:#999;margin-bottom:4px">{s.get("league","")}</div>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-size:12px;font-weight:{'700' if home_w else '400'};color:#1a1714">{s.get("home","")}</td>
              <td align="right" style="font-size:14px;font-weight:700;color:#1a1714">{s.get("homeScore","—")}</td>
            </tr>
            <tr>
              <td style="font-size:12px;font-weight:{'700' if away_w else '400'};color:#1a1714">{s.get("away","")}</td>
              <td align="right" style="font-size:14px;font-weight:700;color:#1a1714">{s.get("awayScore","—")}</td>
            </tr>
          </table>
          <div style="font-family:Arial,sans-serif;font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:0.06em;margin-top:2px">{s.get("status","")}</div>
        </div>"""

    sports_stories_html = "".join(article_html(a, "14px", True) for a in sports.get("stories", [])[:4])

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#d4cfc6;font-family:Georgia,serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#d4cfc6;padding:24px 0">
<tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0" style="background:#f7f4ee;max-width:680px;width:100%">

  <!-- MASTHEAD -->
  <tr><td style="padding:20px 36px 0">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-family:Arial,sans-serif;font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.04em;padding-bottom:8px;border-bottom:1px solid #ccc">{today}</td>
        <td align="center" style="font-family:Arial,sans-serif;font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.04em;padding-bottom:8px;border-bottom:1px solid #ccc">
          <span style="background:#1a1714;color:#f7f4ee;font-size:9px;font-weight:600;letter-spacing:0.1em;padding:2px 7px">PERSONAL EDITION</span>
          &nbsp;Cypress, Texas
        </td>
        <td align="right" style="font-family:Arial,sans-serif;font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.04em;padding-bottom:8px;border-bottom:1px solid #ccc">Est. 2025</td>
      </tr>
    </table>
    <h1 style="font-family:Georgia,serif;font-size:52px;font-weight:900;text-align:center;color:#1a1714;margin:10px 0 4px;line-height:1">The Lundquist Letter</h1>
    <div style="border-top:1px solid #ccc;margin-bottom:0"></div>
    <p style="font-family:Arial,sans-serif;font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:#888;text-align:center;margin:6px 0 0">Manufacturing · Finance · Technology · Science · World Affairs · Sports</p>
  </td></tr>

  <!-- QUOTE -->
  <tr><td style="background:#ede9e0;border-top:2px solid #1a1714;border-bottom:2px solid #1a1714;padding:10px 36px;text-align:center">
    <p style="font-family:Georgia,serif;font-size:14px;font-style:italic;color:#3d3830;margin:0 0 4px;line-height:1.5">"{quote.get("quote","")}"</p>
    <span style="font-family:Arial,sans-serif;font-size:10px;font-weight:500;letter-spacing:0.12em;text-transform:uppercase;color:#999">— {quote.get("author","")}</span>
  </td></tr>

  <!-- MARKETS -->
  <tr><td style="background:#1a1714;padding:8px 36px">
    <table cellpadding="0" cellspacing="0"><tr>
      <td style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#aaa;padding-right:16px;white-space:nowrap">Markets</td>
      <td style="font-family:Arial,sans-serif">{tickers_html}</td>
    </tr></table>
  </td></tr>

  <!-- TOP STORIES -->
  <tr><td style="padding:0 36px">
    <div style="border-top:3px solid #1a1714;padding-top:4px;margin-top:18px;margin-bottom:14px">
      <span style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase">Top Stories</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0"><tr>{top_html}</tr></table>
  </td></tr>

  <!-- DIVIDER -->
  <tr><td style="padding:0 36px"><hr style="border:none;border-top:1px solid #ccc;margin:16px 0 0"></td></tr>

  <!-- MID STORIES -->
  <tr><td style="padding:0 36px">
    <div style="border-top:3px solid #1a1714;padding-top:4px;margin-top:14px;margin-bottom:14px">
      <span style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase">Business · Technology · Science</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0"><tr>{mid_html}</tr></table>
  </td></tr>

  <!-- DIVIDER -->
  <tr><td style="padding:0 36px"><hr style="border:none;border-top:1px solid #ccc;margin:16px 0 0"></td></tr>

  <!-- BOTTOM STORIES -->
  <tr><td style="padding:0 36px">
    <div style="border-top:3px solid #1a1714;padding-top:4px;margin-top:14px;margin-bottom:14px">
      <span style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase">World · Health · Policy</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td valign="top" width="50%">{left_stories}</td>
        <td valign="top" width="50%" style="border-left:1px solid #ddd;padding-left:20px">{right_stories}</td>
      </tr>
    </table>
  </td></tr>

  <!-- DIVIDER -->
  <tr><td style="padding:0 36px"><hr style="border:none;border-top:1px solid #ccc;margin:16px 0 0"></td></tr>

  <!-- SPORTS -->
  <tr><td style="padding:0 36px">
    <div style="border-top:3px solid #1a1714;padding-top:4px;margin-top:14px;margin-bottom:14px">
      <span style="font-family:Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase">Sports</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td valign="top" width="40%" style="padding-right:20px">{scores_html}</td>
        <td valign="top" width="60%" style="border-left:1px solid #ddd;padding-left:20px">{sports_stories_html}</td>
      </tr>
    </table>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding:20px 36px 36px;text-align:center;border-top:3px double #1a1714;margin-top:28px">
    <p style="font-family:Arial,sans-serif;font-size:9px;color:#aaa;letter-spacing:0.06em;margin:0">
      The Lundquist Letter &nbsp;·&nbsp; Curated by Claude &nbsp;·&nbsp; Cypress, Texas<br>
      Click any "Read more →" link to open the full article in your browser.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# ── GMAIL SENDER ─────────────────────────────────────────────────────────────

def get_gmail_service():
    """Build Gmail service from OAuth credentials stored as env vars."""
    creds_json = os.environ.get("GMAIL_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("GMAIL_CREDENTIALS_JSON environment variable not set.")
    creds_data = json.loads(creds_json)
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        scopes=creds_data.get("scopes", ["https://www.googleapis.com/auth/gmail.send"]),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def send_email(service, subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.now().strftime("%A, %B %-d, %Y")
    print(f"📰 Building The Lundquist Letter for {today}…")

    print("  → Fetching quote…")
    quote = fetch_quote(today)

    print("  → Fetching market data…")
    markets = fetch_markets(today)

    print("  → Fetching news articles…")
    articles = fetch_news(today)

    print("  → Fetching sports scores & stories…")
    sports = fetch_sports(today)

    print("  → Building email…")
    html = build_email_html(today, quote, markets, articles, sports)

    print("  → Sending via Gmail…")
    service = get_gmail_service()
    send_email(service, f"The Lundquist Letter — {today}", html)
    print("✅ Done!")


if __name__ == "__main__":
    main()

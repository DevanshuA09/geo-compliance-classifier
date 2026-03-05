"""Download and extract the legal text from a California bill page.

Usage:
	python datascraper.py --url <URL> [--out file.txt]

The extractor uses a few heuristics to find the bill text element and
falls back to searching for the "BILL TEXT" heading in the page.
"""

from __future__ import annotations

import argparse
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Datascraper/1.0; +https://example.com)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def clean_text(text: str) -> str:
    # Normalize whitespace, collapse repeated blank lines to two
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_bill_text_from_soup(soup: BeautifulSoup) -> Optional[str]:
    # Remove scripts/styles/navigation that would pollute the text
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    # Try common id/class selectors first (heuristic)
    selectors = [
        "#billText",
        "#billtext",
        ".bill-text",
        ".BillText",
        "#content",
        "div#content",
        "main",
        "article",
    ]

    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(separator="\n", strip=True)
            if len(txt) > 200:
                return clean_text(txt)

    # Fallback: find a heading that contains 'BILL TEXT' (case-insensitive)
    heading = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if tag.get_text(strip=True).upper().find("BILL TEXT") != -1:
            heading = tag
            break

    if heading:
        parts = []
        # collect following siblings until we hit a navigation block or footer
        for sib in heading.find_all_next():
            # stop if we reached another site section that likely isn't bill text
            if (
                sib.name
                and sib.get("class")
                and any(
                    c.lower().find("nav") != -1 or c.lower().find("vote") != -1
                    for c in sib.get("class")
                )
            ):
                break
            txt = sib.get_text(separator="\n", strip=True)
            if txt:
                parts.append(txt)
            # Heuristic stop: if we've collected a lot and encounter 'Text[Votes]' links area
            if len(parts) > 20 and (
                "Votes" in txt or "Bill PDF" in txt or "Compare Versions" in txt
            ):
                break

        if parts:
            return clean_text("\n\n".join(parts))

    # Generic fallback: return largest text block on page
    candidates = []
    for div in soup.find_all(["div", "section", "article"]):
        txt = div.get_text(separator="\n", strip=True)
        if txt and len(txt) > 200:
            candidates.append((len(txt), txt))
    if candidates:
        candidates.sort(reverse=True)
        return clean_text(candidates[0][1])

    return None


def get_bill_text(url: str) -> str:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = extract_bill_text_from_soup(soup)
    if not text:
        raise RuntimeError("Failed to extract bill text from the page")
    return text


def save_to_file(text: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract bill legal text from a CA Legislature bill page"
    )
    parser.add_argument(
        "--url",
        required=False,
        default="https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB976",
        help="URL of the bill page",
    )
    parser.add_argument("--out", required=False, help="Write output to file")
    args = parser.parse_args()

    text = get_bill_text(args.url)
    if args.out:
        save_to_file(text, args.out)
        print(f"Saved bill text to {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

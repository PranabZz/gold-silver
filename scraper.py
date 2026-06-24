import json
import re
from pathlib import Path
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup


FILE_PATH = "rates.json"


def load_rates():
    """Load existing rates."""
    if not Path(FILE_PATH).exists():
        return []

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, list) else []

    except Exception:
        return []


def save_rates(data):
    """Save rates to file."""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def fetch_rates():
    url = "https://www.fenegosida.org/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text_content = soup.get_text(" ", strip=True)

        gold_match = re.search(
            r"FINE GOLD\s*\(9999\)\s*per 1 tola\s*(?:रु\s*)?([\d,]+)",
            text_content,
            re.IGNORECASE,
        )

        silver_match = re.search(
            r"SILVER\s*per 1 tola\s*(?:रु\s*)?([\d,]+)",
            text_content,
            re.IGNORECASE,
        )

        gold_price = (
            int(gold_match.group(1).replace(",", ""))
            if gold_match
            else None
        )

        silver_price = (
            int(silver_match.group(1).replace(",", ""))
            if silver_match
            else None
        )

        if gold_price is None and silver_price is None:
            raise Exception("Could not extract gold and silver prices")

        rates = load_rates()

        today = date.today().isoformat()

        # Prevent duplicate entries for the same day
        if rates:
            last_date = rates[-1].get("time_stamp", "")[:10]

            if last_date == today:
                print(f"Rate already stored for {today}")
                return

        new_record = {
            "source": "FENEGOSIDA",
            "currency": "NPR",
            "unit": "1 tola",
            "rates": {
                "fine_gold_9999": gold_price,
                "silver": silver_price,
            },
            "timestamp": datetime.utcnow().date().isoformat(),
        }

        rates.append(new_record)

        save_rates(rates)

        print(f"Added rate for {today}")
        print(
            json.dumps(
                new_record,
                indent=4,
                ensure_ascii=False,
            )
        )

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

        print(
            json.dumps(
                error_data,
                indent=4,
                ensure_ascii=False,
            )
        )

        with open(
            "error.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                error_data,
                f,
                ensure_ascii=False,
                indent=4,
            )


if __name__ == "__main__":
    fetch_rates()

import json
import re
from pathlib import Path
from datetime import date

import requests
from bs4 import BeautifulSoup


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
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        today = date.today().isoformat()

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

        gold_price = gold_match.group(1).replace(",", "") if gold_match else None
        silver_price = silver_match.group(1).replace(",", "") if silver_match else None

        new_data = {
            "source": "FENEGOSIDA",
            "currency": "NPR",
            "unit": "1 tola",
            "rates": {
                "fine_gold_9999": gold_price,
                "silver": silver_price,
            },
            "timestamp": today,
        }

        file_path = "rates.json"

        # Load existing data
        if Path(file_path).exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    rates = json.load(f)

                    if not isinstance(rates, list):
                        rates = []

                except json.JSONDecodeError:
                    rates = []
        else:
            rates = []

        # Check if today's entry already exists
        exists = any(
            item.get("time_stamp") == today
            for item in rates
        )

        if not exists:
            rates.append(new_data)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rates, f, ensure_ascii=False, indent=4)

            print(f"Added new record for {today}")
        else:
            print(f"Record for {today} already exists")

        print(json.dumps(new_data, indent=4, ensure_ascii=False))

    except Exception as e:
        error_data = {
            "error": str(e),
            "time_stamp": date.today().isoformat(),
        }

        print(json.dumps(error_data, indent=4))

        with open("error.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    fetch_rates()

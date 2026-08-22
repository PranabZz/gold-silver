import json
import re
from pathlib import Path
from datetime import datetime, timezone

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
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_from_today_api(session, headers):
    """Fetch rates from the FENEGOSIDA Dashboard/today API endpoint."""
    url = "https://api.fenegosida.org/api/website/v1/Dashboard/today"
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list) or not data:
        return None, None, None

    gold_price = None
    silver_price = None
    rate_date = None

    for item in data:
        rate_type = item.get("rateType", "")
        date_str = item.get("todayDate", "")
        if date_str and not rate_date:
            rate_date = date_str[:10]

        val = item.get("todayBaseRatePerGram")
        if val is not None:
            val = int(val) if val == int(val) else val
            # Rate for 10 grams (standard base rate stored in rates.json)
            if ("सुन" in rate_type or "gold" in rate_type.lower()) and (
                "१० ग्राम" in rate_type or "10 gm" in rate_type.lower() or "10gm" in rate_type.lower() or "10 gram" in rate_type.lower()
            ):
                gold_price = val
            elif ("चाँदी" in rate_type or "silver" in rate_type.lower()) and (
                "१० ग्राम" in rate_type or "10 gm" in rate_type.lower() or "10gm" in rate_type.lower() or "10 gram" in rate_type.lower()
            ):
                silver_price = val

    return gold_price, silver_price, rate_date


def fetch_from_weekly_api(session, headers):
    """Fetch latest rates from WeeklyChartRate API as fallback."""
    url = "https://api.fenegosida.org/api/website/v1/Dashboard/WeeklyChartRate?weekmonthyear=1"
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    gold_data = data.get("goldData", [])
    silver_data = data.get("silverData", [])

    if not gold_data and not silver_data:
        return None, None, None

    gold_entry = gold_data[-1] if gold_data else {}
    silver_entry = silver_data[-1] if silver_data else {}

    gold_price = gold_entry.get("gm")
    if gold_price is not None:
        gold_price = int(gold_price) if gold_price == int(gold_price) else gold_price

    silver_price = silver_entry.get("gm")
    if silver_price is not None:
        silver_price = int(silver_price) if silver_price == int(silver_price) else silver_price

    # Formulate date YYYY-MM-DD from year, month, date
    year = gold_entry.get("year") or silver_entry.get("year")
    month = gold_entry.get("month") or silver_entry.get("month")
    day = gold_entry.get("date") or silver_entry.get("date")

    rate_date = None
    if year and month and day:
        try:
            parsed = datetime.strptime(f"{year}-{month}-{day.zfill(2)}", "%Y-%b-%d")
            rate_date = parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

    return gold_price, silver_price, rate_date


def fetch_from_html(session, headers):
    """Fetch rates from HTML page regex as fallback."""
    url = "https://www.fenegosida.org/"
    response = session.get(url, headers=headers, timeout=30)
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
        int(gold_match.group(1).replace(",", "")) if gold_match else None
    )

    silver_price = (
        int(silver_match.group(1).replace(",", "")) if silver_match else None
    )

    return gold_price, silver_price, None


def fetch_rates():
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.fenegosida.org/",
        "Origin": "https://www.fenegosida.org",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        gold_price = None
        silver_price = None
        rate_date = None

        # 1. Try Today API
        try:
            gold_price, silver_price, rate_date = fetch_from_today_api(session, headers)
        except Exception as e:
            print(f"Today API failed: {e}")

        # 2. Try Weekly API fallback
        if gold_price is None and silver_price is None:
            try:
                gold_price, silver_price, rate_date = fetch_from_weekly_api(session, headers)
            except Exception as e:
                print(f"Weekly API fallback failed: {e}")

        # 3. Try HTML scraping fallback
        if gold_price is None and silver_price is None:
            try:
                gold_price, silver_price, _ = fetch_from_html(session, headers)
            except Exception as e:
                print(f"HTML fallback failed: {e}")

        if gold_price is None and silver_price is None:
            raise Exception("Could not extract gold and silver prices from any source")

        if not rate_date:
            rate_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        rates = load_rates()

        # Prevent duplicate entries for the same date
        if any(r.get("timestamp") == rate_date for r in rates):
            print(f"Rate already stored for {rate_date}")
            return

        new_record = {
            "source": "FENEGOSIDA",
            "currency": "NPR",
            "unit": "1 tola",
            "rates": {
                "fine_gold_9999": gold_price,
                "silver": silver_price,
            },
            "timestamp": rate_date,
        }

        rates.append(new_record)
        save_rates(rates)

        print(f"Added rate for {rate_date}")
        print(json.dumps(new_record, indent=2, ensure_ascii=False))

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        print(json.dumps(error_data, indent=2, ensure_ascii=False))

        with open("error.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    fetch_rates()


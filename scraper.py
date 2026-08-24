import json
from pathlib import Path
from datetime import datetime, timezone
import requests

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
        return None

    rates_data = {
        "10g": {"fine_gold_9999": None, "silver": None},
        "1 tola": {"fine_gold_9999": None, "silver": None},
        "date": None
    }

    for item in data:
        rate_type = item.get("rateType", "")
        date_str = item.get("todayDate", "")
        if date_str and not rates_data["date"]:
            rates_data["date"] = date_str[:10]

        val = item.get("todayBaseRatePerGram")
        if val is not None:
            val = int(val) if val == int(val) else val
            
            # Gold vs Silver check
            is_gold = "सुन" in rate_type or "gold" in rate_type.lower()
            is_silver = "चाँदी" in rate_type or "silver" in rate_type.lower()
            
            # Unit check (10g vs 1 tola)
            is_10g = "१० ग्राम" in rate_type or "10 gm" in rate_type.lower() or "10gm" in rate_type.lower() or "10 gram" in rate_type.lower()
            is_1tola = "१ तोला" in rate_type or "1 tola" in rate_type.lower() or "1tola" in rate_type.lower()

            if is_gold:
                if is_10g:
                    rates_data["10g"]["fine_gold_9999"] = val
                elif is_1tola:
                    rates_data["1 tola"]["fine_gold_9999"] = val
            elif is_silver:
                if is_10g:
                    rates_data["10g"]["silver"] = val
                elif is_1tola:
                    rates_data["1 tola"]["silver"] = val

    # Verify if we found all prices
    if (rates_data["10g"]["fine_gold_9999"] is not None and
        rates_data["10g"]["silver"] is not None and
        rates_data["1 tola"]["fine_gold_9999"] is not None and
        rates_data["1 tola"]["silver"] is not None):
        return rates_data
    
    return None


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
        rates_data = fetch_from_today_api(session, headers)
        if not rates_data:
            raise Exception("Could not extract all gold and silver prices from today API")

        rate_date = rates_data["date"]
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
            "timestamp": rate_date,
            "rates": {
                "10g": {
                    "fine_gold_9999": rates_data["10g"]["fine_gold_9999"],
                    "silver": rates_data["10g"]["silver"],
                },
                "1 tola": {
                    "fine_gold_9999": rates_data["1 tola"]["fine_gold_9999"],
                    "silver": rates_data["1 tola"]["silver"],
                }
            }
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

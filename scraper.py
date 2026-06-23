import requests
from bs4 import BeautifulSoup

def fetch_rates():
    url = "https://www.fenegosida.org/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Note: These class/tag selectors are generalized based on standard layouts. 
        # You may need to inspect the exact HTML of the site if classes differ.
        print("--- FENEGOSIDA Gold & Silver Rates ---")
        
        # Searching text content to find the prices accurately
        text_content = soup.get_text()
        
        # Fallback raw dump or target extraction if specific elements are known
        # Let's print out what we found to logs
        for rate_box in soup.find_all(class_=["rate-box", "gold-rate", "price"]):
            print(rate_box.text.strip())
            
        # Example of targeted extraction (adjust selectors based on inspecting the site's exact code)
        # print(soup.find(text="FINE GOLD (9999)").find_next().text)
        
        print("\nFull Page Fetch Successful. Check logs above.")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_rates()

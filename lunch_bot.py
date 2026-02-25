import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# --- KONFIGURATION (Hämtas från GitHub Secrets) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_swedish_day():
    # Returnerar dagens namn på svenska för att matcha hemsidorna
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now().weekday()]

def scrape_sodra_porten():
    """Hämtar meny från Södra Porten via Kvartersmenyn."""
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Leta efter rubriken för rätt dag
        day_header = soup.find('h3', string=day_name)
        if not day_header:
            return "Kunde inte hitta menyn för idag (Södra Porten)."
        
        # Menyn ligger i nästa div med klassen menu_perc_div
        menu_div = day_header.find_next_sibling('div', class_='menu_perc_div')
        if not menu_div:
            return "Menyn hittades men formatet var oväntat (Södra Porten)."

        items = menu_div.find_all('p')
        menu_text = ""
        for item in items:
            txt = item.get_text(strip=True)
            if txt:
                # Snygga till texten och ta bort ev. radbrytningar i rätten
                menu_text += f"• {txt.replace(chr(10), ' ')}\n"
        
        return menu_text if menu_text else "Menyn verkar vara tom för idag."
    except Exception as e:
        return f"Fel vid hämtning från Södra Porten: {e}"

def scrape_nya_etage():
    """Hämtar meny från Nya Etage."""
    try:
        url = "https://nyaetage.se/"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Nya Etage har ofta dagen inuti en <h4> eller <strong>
        day_tag = soup.find(lambda tag: tag.name in ['h4', 'strong', 'p'] and day_name in tag.text)
        
        if not day_tag:
            return "Kunde inte hitta menyn för idag (Nya Etage)."
        
        menu_items = []
        # Gå igenom nästkommande <p>-taggar tills vi når nästa dag eller slut på menyn
        current = day_tag.find_next('p')
        while current:
            text = current.get_text(strip=True)
            # Sluta om vi ser en annan veckodag
            if any(d in text for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]) and text != day_name:
                break
            if text and text != day_name:
                menu_items.append(f"• {text}")
            current = current.find_next('p')
            
        return "\n".join(menu_items) if menu_items else "Kunde inte extrahera rätterna (Nya Etage)."
    except Exception as e:
        return f"Fel vid hämtning från Nya Etage: {e}"

async def main():
    day = get_swedish_day()
    
    # Kör inte på helger
    if day in ["Lördag", "Söndag"]:
        print(f"Det är {day}, ingen lunchrapport skickas.")
        return

    if not TOKEN or not CHAT_ID:
        print("Fel: TOKEN eller CHAT_ID saknas i miljövariablerna!")
        return

    bot = Bot(token=TOKEN)
    
    print(f"Hämtar menyer för {day}...")
    sodra = scrape_sodra_porten()
    etage = scrape_nya_etage()
    
    meddelande = (
        f"🍴 *LUNCH {day.upper()}* 🍴\n\n"
        f"📍 *Restaurang Södra Porten*\n{sodra}\n\n"
        f"📍 *Restaurang Nya Etage*\n{etage}\n\n"
        "Smaklig måltid!"
    )
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=meddelande, parse_mode='Markdown')
        print("Rapporten har skickats till Telegram!")
    except Exception as e:
        print(f"Telegram-fel: {e}")

if __name__ == "__main__":
    asyncio.run(main())

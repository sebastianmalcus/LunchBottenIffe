import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# --- KONFIGURATION ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_swedish_day():
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now().weekday()]

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Söker efter dagen oavsett stora/små bokstäver
        day_header = soup.find(lambda tag: tag.name == "h3" and day_name.lower() in tag.text.lower())
        
        if not day_header:
            return f"Hittade inte sektionen för {day_name}."
        
        menu_div = day_header.find_next_sibling('div', class_='menu_perc_div')
        items = menu_div.find_all('p')
        
        menu_text = ""
        for item in items:
            txt = item.get_text(strip=True)
            if txt and len(txt) > 3: # Ignorerar tomma eller för korta rader
                menu_text += f"• {txt}\n"
        
        return menu_text if menu_text else "Menyn är tom för idag."
    except Exception as e:
        return f"Fel: {e}"

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Letar efter dagen i h4, strong eller p
        day_tag = soup.find(lambda tag: tag.name in ['h4', 'strong', 'p'] and day_name.lower() in tag.text.lower())
        
        if not day_tag:
            return f"Hittade inte sektionen för {day_name}."
        
        menu_items = []
        current = day_tag.find_next('p')
        # Samla ihop alla rader tills vi når nästa dag
        while current:
            text = current.get_text(strip=True)
            if any(d in text for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]) and text.lower() != day_name.lower():
                break
            if text and text.lower() != day_name.lower():
                menu_items.append(f"• {text}")
            current = current.find_next('p')
            
        return "\n".join(menu_items) if menu_items else "Kunde inte läsa rätterna."
    except Exception as e:
        return f"Fel: {e}"

async def main():
    day = get_swedish_day()
    if day in ["Lördag", "Söndag"]: return

    bot = Bot(token=TOKEN)
    sodra = scrape_sodra_porten()
    etage = scrape_nya_etage()
    
    meddelande = (
        f"🍴 *LUNCH {day.upper()}* 🍴\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=meddelande, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())

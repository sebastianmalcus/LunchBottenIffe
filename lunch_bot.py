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
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Kvartersmenyn kan ha dagen i h3 eller h4
        day_header = soup.find(lambda tag: tag.name in ["h3", "h4"] and day_name.lower() in tag.text.lower())
        
        if not day_header:
            return f"⚠️ Hittade ingen meny för {day_name} på sidan just nu."
        
        menu_div = day_header.find_next_sibling('div')
        if not menu_div:
            return "⚠️ Hittade dagen men inte rätterna."

        items = menu_div.find_all('p')
        menu_text = ""
        for item in items:
            txt = item.get_text(strip=True)
            if len(txt) > 5: # Ignorera korta rader som "Vegetariskt" om rätten saknas
                menu_text += f"• {txt}\n"
        
        return menu_text if menu_text else "Menyn verkar vara tom för tillfället."
    except Exception as e:
        return f"❌ Tekniskt fel: {e}"

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Nya Etage är lite luriga med sina taggar
        day_tag = soup.find(lambda tag: day_name.lower() in tag.text.lower() and tag.name in ['h4', 'strong', 'p', 'span'])
        
        if not day_tag:
            return f"⚠️ Menyn för {day_name} verkar inte vara uppladdad än."
        
        menu_items = []
        # Vi letar efter rätter i de efterföljande elementen
        current = day_tag.find_next(['p', 'div'])
        while current:
            text = current.get_text(strip=True)
            # Stoppa om vi krockar med nästa dag
            if any(d in text for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]) and text.lower() != day_name.lower():
                break
            if text and len(text) > 5 and text.lower() != day_name.lower():
                menu_items.append(f"• {text}")
            current = current.find_next(['p', 'div'])
            
        return "\n".join(menu_items) if menu_items else "Kunde inte läsa ut rätterna."
    except Exception as e:
        return f"❌ Tekniskt fel: {e}"

async def main():
    day = get_swedish_day()
    if day in ["Lördag", "Söndag"]: 
        print("Helg!")
        return

    if not TOKEN or not CHAT_ID:
        print("Saknar Token/ChatID")
        return

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

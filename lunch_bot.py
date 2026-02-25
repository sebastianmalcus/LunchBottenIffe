import asyncio
import requests
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_swedish_day():
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now().weekday()]

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Hitta rubriken som innehåller dagens namn
        target = soup.find(lambda t: t.name in ['h3', 'h4', 'strong'] and day_name.lower() in t.get_text().lower())
        
        if target:
            menu_items = []
            # Kvartersmenyn lägger ofta rätterna i efterföljande p-taggar
            current = target.find_next('p')
            count = 0
            while current and count < 10:
                text = current.get_text(strip=True)
                # Om vi stöter på nästa veckodag, avbryt
                if any(d in text for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]) and day_name.lower() not in text.lower():
                    break
                if len(text) > 4:
                    menu_items.append(f"• {text}")
                current = current.find_next('p')
                count += 1
            
            if menu_items: return "\n".join(menu_items)
            
        return "Kunde inte extrahera rätterna, men sidan är uppe."
    except Exception as e:
        return f"Fel vid skrapning: {str(e)}"

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Nya Etage har "Onsdag IDAG". Vi letar efter containern som har dagens namn.
        day_box_header = soup.find(lambda t: t.name == 'h3' and day_name.lower() in t.get_text().lower())
        
        if day_box_header:
            # Gå upp till boxen (div) och hitta alla rader
            parent = day_box_header.find_parent('div')
            if not parent: parent = day_box_header.parent
            
            items = parent.find_all(['li', 'p'])
            menu_text = []
            for i in items:
                txt = i.get_text(strip=True)
                # Rensa bort rubriken själv och korta ord
                if day_name.lower() not in txt.lower() and len(txt) > 3:
                    # Ta bort ">" tecken som de använder som bullets
                    clean_txt = txt.lstrip('>').strip()
                    menu_text.append(f"• {clean_txt}")
            
            if menu_text: return "\n".join(menu_text)

        return "Hittade boxen men inga rätter. Kolla formatet."
    except Exception as e:
        return f"Fel vid skrapning: {str(e)}"

async def main():
    if get_swedish_day() in ["Lördag", "Söndag"]: return
    
    bot = Bot(token=TOKEN)
    
    # Hämta menyer
    sodra = scrape_sodra_porten()
    etage = scrape_nya_etage()
    
    msg = (
        f"🍴 *LUNCH {get_swedish_day().upper()}* 🍴\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())

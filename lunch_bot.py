import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_number():
    return datetime.now().weekday() + 1

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8' 
        soup = BeautifulSoup(res.text, 'html.parser')
        
        day_num = get_day_number()
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        
        if not day_card:
            return "⚠️ Hittade inte dagens meny-kort."

        items_container = day_card.find('div', class_='menu-items')
        if not items_container:
            return "⚠️ Hittade inte rätterna i boxen."

        dagens = []
        veggo = ""
        
        for text in items_container.stripped_strings:
            text = text.lstrip('>').lstrip('•').strip().replace('*', '').replace('_', '')
            if len(text) > 5 and text.lower() != "idag":
                if "veg/" in text.lower() or "vegan" in text.lower():
                    if text not in veggo:
                        veggo = f"\n🥗 *Vegetariskt*\n• {text}"
                else:
                    if f"• {text}" not in dagens:
                        dagens.append(f"• {text}")

        meny = "\n".join(dagens)
        if veggo:
            meny += veggo
            
        return meny if meny else "⚠️ Inga rätter hittades."
    except Exception as e:
        return f"❌ Fel vid skrapning: {str(e)}"

def scrape_sodra_porten():
    try:
        # NYA OFFICIELLA LÄNKEN
        url = "https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/sodra-porten/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today_str = days[datetime.now().weekday()].lower()
        
        # 1. Sök upp rätt veckodag
        day_tag = soup.find(lambda t: t.name in ['h2', 'h3', 'h4', 'span', 'strong', 'div', 'button'] and t.get_text(strip=True).lower() == today_str)
        if not day_tag:
            day_tag = soup.find(lambda t: t.name in ['h2', 'h3', 'h4', 'span', 'strong', 'div', 'button'] and t.get_text(strip=True).lower().startswith(today_str))

        if not day_tag:
            return "⚠️ Hittade inte dagens rubrik på nya hemsidan."
            
        # 2. Hitta boxen som innehåller maten (Gå uppåt i koden tills vi hittar en div med mycket text)
        container = day_tag.parent
        for _ in range(4):
            if container and len(container.get_text(strip=True)) > 150:
                break
            container = container.parent if container else None
            
        if not container:
            container = soup.body

        menu_items = []
        capture = False
        
        # Ord vi vill kasta i papperskorgen (Compass Group har mycket näringsinfo vi inte vill visa)
        ignore_words = [
            "grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", 
            "klimatpåverkan", "energifördelning", "andel av", "stäng", "välkomna", "tel:"
        ]
        
        # 3. Läs texten
        for text in container.stripped_strings:
            clean_text = text.replace('\xa0', ' ').replace('*', '').replace('_', '').replace('"', '').strip()
            if not clean_text:
                continue
                
            lower_text = clean_text.lower()
            
            # Är det en veckodag?
            is_day = False
            for d in days:
                dl = d.lower()
                if lower_text == dl or lower_text.startswith(dl + ":") or lower_text.startswith(dl + " "):
                    is_day = True
                    if dl == today_str:
                        capture = True
                    else:
                        capture = False
                    break
                    
            if is_day:
                continue
                
            if capture:
                # Filtrera och plocka maten
                if len(clean_text) > 10:
                    if not any(lower_text.startswith(iw) for iw in ignore_words):
                        # Extra säkerhet för att ta bort Compass Groups specifika näringsinfo
                        if "klimatpåverkan" not in lower_text and "dagligt behov" not in lower_text:
                            if f"• {clean_text}" not in menu_items:
                                menu_items.append(f"• {clean_text}")
                                
        return "\n".join(menu_items) if menu_items else "⚠️ Koden läste nya rutan men hittade inga rätter."
    except Exception as e:
        return f"❌ Fel: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: 
        return 
    
    bot = Bot(token=TOKEN)
    etage = scrape_nya_etage()
    sodra = scrape_sodra_porten()
    
    dag = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"][datetime.now().weekday()]
    
    msg = (
        f"🍴 *LUNCH {dag}* 🍴\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import requests
import os
from bs4 import BeautifulSoup, NavigableString, Tag
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
        url = "https://sodraporten.kvartersmenyn.se/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()].lower()
        
        menu_div = soup.find('div', class_='meny')
        if not menu_div:
            return "⚠️ Hittade inte meny-containern på sidan."

        menu_items = []
        capture = False
        
        # Städa bort deras rubriker (exakt enligt din bild)
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "öppet", "***", "husmanskost"]
        
        # Vi itererar exakt enligt ordningen i HTML-trädet på din bild
        for child in menu_div.children:
            text = ""
            
            # 1. Om det är en tagg (t.ex. <strong>Onsdag</strong>)
            if isinstance(child, Tag) and child.name in ['strong', 'b', 'h3', 'p']:
                text = child.get_text(strip=True)
            # 2. Om det är lös text (som maträtterna på din bild)
            elif isinstance(child, NavigableString):
                text = str(child).strip()
                
            if not text:
                continue

            lower_text = text.lower().replace(':', '')
            
            # Kolla om vi hittar en dag
            matched_day = False
            for d in days:
                if lower_text == d.lower() or lower_text.startswith(d.lower()):
                    matched_day = True
                    if d.lower() == today:
                        capture = True
                    else:
                        capture = False # Vi har nått en annan dag
                    break
                    
            if matched_day:
                continue
                
            # 3. Fånga BARA den rena texten (NavigableString), detta hoppar över <i>pogre</i> och <br> automatiskt!
            if capture and isinstance(child, NavigableString) and len(text) > 8:
                clean_text = text.replace('*', '').replace('_', '')
                lower_clean = clean_text.lower()
                
                # Sålla bort "Grönt och gott" osv
                if not any(lower_clean.startswith(iw) for iw in ignore_words):
                    item = f"• {clean_text}"
                    if item not in menu_items:
                        menu_items.append(item)
                        
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades för idag."
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

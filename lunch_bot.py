import asyncio
import requests
import os
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
        day = get_swedish_day()
        
        # Försök hitta specifik dag
        header = soup.find(lambda t: t.name in ["h3", "h4"] and day.lower() in t.text.lower())
        if header:
            menu = header.find_next_sibling('div')
            if menu:
                txt = "\n".join([f"• {p.get_text(strip=True)}" for p in menu.find_all('p') if len(p.get_text()) > 3])
                if txt: return txt

        # Backup: Hämta hela veckans text om dagen saknas
        all_text = soup.find('div', class_='menu_perc_div')
        return "Veckans meny:\n" + all_text.get_text(separator="\n", strip=True)[:300] + "..." if all_text else "Ingen meny tillgänglig."
    except: return "Kunde inte hämta från Södra Porten."

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        day = get_swedish_day()
        
        tag = soup.find(lambda t: day.lower() in t.text.lower() and t.name in ['h4', 'strong', 'p'])
        if tag:
            items = []
            curr = tag.find_next('p')
            while curr and not any(d in curr.text for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"] if d != day):
                t = curr.get_text(strip=True)
                if t and t != day: items.append(f"• {t}")
                curr = curr.find_next('p')
            if items: return "\n".join(items)

        return "Besök https://nyaetage.se/ för veckomenyn (ej uppdaterad dag-för-dag än)."
    except: return "Kunde inte hämta från Nya Etage."

async def main():
    if get_swedish_day() in ["Lördag", "Söndag"]: return
    bot = Bot(token=TOKEN)
    msg = f"🍴 *LUNCH {get_swedish_day().upper()}* 🍴\n\n📍 *Södra Porten*\n{scrape_sodra_porten()}\n\n📍 *Nya Etage*\n{scrape_nya_etage()}\n\nSmaklig måltid!"
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())

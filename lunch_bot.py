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
url = ""
res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, 'html.parser')

def scrape_sodra_porten():
try:
url = ""
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0'}
html = ""

async def main():
if datetime.now().weekday() >= 5:
return

if name == "main":
asyncio.run(main())

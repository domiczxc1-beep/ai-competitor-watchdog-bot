import os
import re
import sqlite3
import logging
import threading
import time
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHECK_INTERVAL = 3600  # Интервал проверки в секундах (1 час)

bot = telebot.TeleBot(BOT_TOKEN)
DB_NAME = "watchdog.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            target_price REAL,
            last_price REAL,
            title TEXT
        )
    ''')
    conn.commit()
    conn.close()

def parse_page(url):
    """
    Парсит страницу товара и извлекает заголовок и цену.
    В продакшн-версии интегрируется OpenAI API для анализа неструктурированного HTML.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Получение заголовка страницы
        title = soup.title.string.strip() if soup.title else "Товар по ссылке"
        if len(title) > 50:
            title = title[:47] + "..."
            
        # Поиск чисел, похожих на цену (простая эвристика)
        text = soup.get_text()
        prices = re.findall(r'(\d+[\s\d]*[.,]?\d*)\s*(?:₽|руб|USD|\$|EUR|€)', text)
        
        found_price = None
        if prices:
            clean_price = prices[0].replace(' ', '').replace(',', '.')
            try:
                found_price = float(clean_price)
            except ValueError:
                found_price = None
                
        return title, found_price
    except Exception as e:
        logging.error(f"Ошибка при парсинге {url}: {e}")
        return None, None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 <b>Добро пожаловать в Competitor Watchdog AI!</b>\n\n"
        "Я помогу вам следить за ценами конкурентов на любых сайтах.\n\n"
        "<b>Команды:</b>\n"
        "/add [URL] [Целевая цена] - Добавить ссылку для отслеживания\n"
        "/list - Список ваших отслеживаемых товаров\n"
        "/check - Принудительно проверить цены прямо сейчас\n"
    )
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['add'])
def add_item(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠️ Использование: `/add <URL> [целевая_цена]`", parse_mode='Markdown')
        return
        
    url = args[0]
    target_price = float(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    bot.reply_to(message, "🔍 Анализирую страницу...")
    title, current_price = parse_page(url)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tracked_items (user_id, url, target_price, last_price, title)
        VALUES (?, ?, ?, ?, ?)
    ''', (message.chat.id, url, target_price, current_price, title))
    conn.commit()
    conn.close()
    
    price_str = f"{current_price} руб." if current_price else "Не удалось определить"
    bot.send_message(
        message.chat.id,
        f"✅ <b>Товар добавлен!</b>\n\n📌 <b>Название:</b> {title}\n💰 <b>Текущая цена:</b> {price_str}",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['list'])
def list_items(message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, last_price, target_price FROM tracked_items WHERE user_id = ?', (message.chat.id,))
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        bot.reply_to(message, "🚀 У вас пока нет отслеживаемых товаров.")
        return
        
    response = "📋 <b>Ваши товары:</b>\n\n"
    for item in items:
        item_id, title, price, target = item
        price_info = f"{price} руб." if price else "N/A"
        target_info = f"(Цель: {target} руб.)" if target else ""
        response += f"<b>#{item_id}</b> {title}\n💰 Цена: {price_info} {target_info}\n\n"
        
    bot.send_message(message.chat.id, response, parse_mode='HTML')

def background_checker():
    """Фоновый поток для периодической проверки цен."""
    while True:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, url, target_price, last_price, title FROM tracked_items')
            items = cursor.fetchall()
            
            for item in items:
                item_id, user_id, url, target_price, last_price, title = item
                _, new_price = parse_page(url)
                
                if new_price is not None and new_price != last_price:
                    cursor.execute('UPDATE tracked_items SET last_price = ? WHERE id = ?', (new_price, item_id))
                    conn.commit()
                    
                    # Уведомление об изменении цены
                    diff = new_price - (last_price or new_price)
                    icon = "📉" if diff < 0 else "📈"
                    bot.send_message(
                        user_id,
                        f"{icon} <b>Изменение цены!</b>\n\n"
                        f"📌 <b>Товар:</b> {title}\n"
                        f"💵 <b>Старая цена:</b> {last_price} руб.\n"
                        f"✨ <b>Новая цена:</b> {new_price} руб.",
                        parse_mode='HTML'
                    )
            conn.close()
        except Exception as e:
            logging.error(f"Ошибка background_checker: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    init_db()
    # Запуск проверки цен в отдельном потоке
    threading.Thread(target=background_checker, daemon=True).start()
    logging.info("Бот запущен...")
    bot.infinity_polling()

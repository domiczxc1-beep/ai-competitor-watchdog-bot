# AI Competitor Watchdog Bot 🛡️💰

Инструмент автоматизации и продуктовой аналитики для селлеров (Wildberries, Ozon, Shopify) и владельцев e-commerce бизнеса.

## 🎯 Продуктовая ценность и монетизация

### Проблема
Малый и средний бизнес в e-commerce теряет до 15% выручки из-за несвоевременной реакции на демпинг со стороны конкурентов или изменения стоимости закупок.

### Решение
Micro-SaaS Telegram-бот, который мониторит целевые страницы товаров 24/7, распознает цены и извещает селлера при любых изменениях или достижении пороговой цены.

### Бизнес-модель (Freemium):
- **Free Plan**: До 3 товаров, проверка 1 раз в 12 часов.
- **PRO Plan ($9.99/мес)**: До 50 товаров, проверка каждые 15 минут, уведомления в Telegram + экспорт истории цен в CSV.
- **Enterprise Plan ($29.99/мес)**: Неограниченно, интеграция с OpenAI API для сложного парсинга динамического JS-контента и умной аналитики активов.

---

## 🛠️ Технологический стек
- **Backend**: Python 3.10+
- **Telegram Bot API**: `pyTelegramBotAPI`
- **Parsing Engine**: `requests`, `BeautifulSoup4` (с возможностью подключения LLM OpenAI для парсинга нестандартной верстки)
- **Database**: SQLite / PostgreSQL

---

## 🚀 Быстрый запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/your-username/ai-competitor-watchdog-bot.git
   cd ai-competitor-watchdog-bot
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте переменные окружения:**
   Установите токен вашего бота от `@BotFather`:
   ```bash
   export BOT_TOKEN="your_telegram_bot_token_here"
   ```

4. **Запустите бота:**
   ```bash
   python main.py
   ```

# Ainur Landing

Лендинг для позиционирования `Ainur` как интегратора AI-решений для бизнеса.

## Stack

- Next.js 15
- React 19
- TypeScript
- Drizzle ORM + libSQL
- Resend API + Telegram Bot API

## Concepts

- Основной визуальный вариант сейчас лежит в `concepts/friendly-cyberpunk-v1/`.
- Корневой маршрут `/` просто экспортирует этот концепт.
- Отдельный preview-route: `/concepts/friendly-cyberpunk-v1`.

## Local start

```bash
npm install
npm run dev
```

## Lead delivery

- Все заявки сохраняются в локальную SQLite-базу (`data/leads.db`), если не указан иной `DATABASE_URL`.
- Email-уведомление включается через `RESEND_API_KEY` и `LEAD_EMAIL_FROM`.
- Telegram-уведомление включается через `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.
- Без настроенных внешних каналов заявка всё равно сохраняется, а API вернёт `delivery_error`.

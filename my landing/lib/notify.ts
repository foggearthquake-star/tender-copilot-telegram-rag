import type { LeadRecord } from "@/lib/types";

function buildLeadMessage(lead: LeadRecord) {
  return [
    `Новая заявка с лендинга Ainur`,
    ``,
    `ID: ${lead.id}`,
    `Имя: ${lead.name}`,
    `Компания: ${lead.company}`,
    `Контакт: ${lead.telegram_or_email}`,
    `Бюджет: ${lead.budget_range || "Нужно обсудить"}`,
    `Источник: ${lead.source}`,
    `Создано: ${lead.created_at}`,
    ``,
    `Задача:`,
    `${lead.project_summary}`,
  ].join("\n");
}

async function sendEmailNotification(message: string) {
  const { RESEND_API_KEY, LEAD_EMAIL_FROM, LEAD_EMAIL_TO } = process.env;

  if (!RESEND_API_KEY || !LEAD_EMAIL_FROM) {
    return false;
  }
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: LEAD_EMAIL_FROM,
      to: [LEAD_EMAIL_TO || "foggearthquake@gmail.com"],
      subject: "Новая заявка с landing Ainur",
      text: message,
    }),
  });

  if (!response.ok) {
    throw new Error(`Email delivery failed with status ${response.status}`);
  }

  return true;
}

async function sendTelegramNotification(message: string) {
  const { TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;

  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    return false;
  }

  const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: message,
    }),
  });

  if (!response.ok) {
    throw new Error(`Telegram delivery failed with status ${response.status}`);
  }

  return true;
}

export async function notifyLead(lead: LeadRecord) {
  const message = buildLeadMessage(lead);
  const results = await Promise.allSettled([sendEmailNotification(message), sendTelegramNotification(message)]);

  const delivered = results.some((result) => result.status === "fulfilled" && result.value);
  const failures = results.filter((result) => result.status === "rejected");

  return {
    delivered,
    failures,
  };
}

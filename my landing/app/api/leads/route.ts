import { createHash } from "node:crypto";

import { NextRequest, NextResponse } from "next/server";

import { createLead } from "@/lib/db/repository";
import { notifyLead } from "@/lib/notify";
import { checkRateLimit } from "@/lib/rate-limit";
import type { LeadApiResponse, LeadRecord } from "@/lib/types";
import { leadSchema } from "@/lib/validation";

function getClientIp(request: NextRequest) {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return forwardedFor.split(",")[0]?.trim() || "unknown";
  }

  return request.headers.get("x-real-ip") || "unknown";
}

function hashIp(ip: string) {
  return createHash("sha256").update(ip).digest("hex");
}

export async function POST(request: NextRequest) {
  const ip = getClientIp(request);
  const rateResult = checkRateLimit(ip);

  if (!rateResult.ok) {
    return NextResponse.json<LeadApiResponse>(
      {
        status: "throttled",
        message: "Слишком много попыток за короткое время. Повторите отправку чуть позже.",
      },
      { status: 429 },
    );
  }

  const body = await request.json().catch(() => null);
  const parsed = leadSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json<LeadApiResponse>(
      {
        status: "validation_error",
        message: "Проверьте поля формы: контакт, описание задачи и согласие на обработку должны быть заполнены корректно.",
      },
      { status: 400 },
    );
  }

  if (parsed.data.website) {
    return NextResponse.json<LeadApiResponse>({
      status: "success",
      message: "Заявка принята.",
    });
  }

  const saved = await createLead(parsed.data, hashIp(ip), "landing:v1");
  const leadRecord: LeadRecord = {
    id: saved.id,
    name: saved.name,
    company: saved.company,
    telegram_or_email: saved.telegramOrEmail,
    project_summary: saved.projectSummary,
    budget_range: saved.budgetRange,
    consent: saved.consent === "true",
    source: saved.source,
    ip_hash: saved.ipHash,
    created_at: saved.createdAt,
  };

  const notification = await notifyLead(leadRecord);

  if (!notification.delivered) {
    return NextResponse.json<LeadApiResponse>({
      status: "delivery_error",
      message:
        "Заявка сохранена, но внешний канал доставки сейчас не подтвердился. Я всё равно увижу её в системе и свяжусь вручную.",
    });
  }

  return NextResponse.json<LeadApiResponse>({
    status: "success",
    message: "Заявка отправлена. Можешь продублировать задачу в Telegram, если нужен быстрый контакт.",
  });
}

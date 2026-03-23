import { randomUUID } from "node:crypto";

import { desc, sql } from "drizzle-orm";

import { db } from "@/lib/db/client";
import { leads } from "@/lib/db/schema";
import type { LeadInput } from "@/lib/validation";

async function ensureSchema() {
  await db.run(sql`
    CREATE TABLE IF NOT EXISTS leads (
      id TEXT PRIMARY KEY NOT NULL,
      name TEXT NOT NULL,
      company TEXT NOT NULL,
      telegram_or_email TEXT NOT NULL,
      project_summary TEXT NOT NULL,
      budget_range TEXT NOT NULL,
      consent TEXT NOT NULL DEFAULT 'true',
      source TEXT NOT NULL,
      ip_hash TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

export async function createLead(payload: LeadInput, ipHash: string, source: string) {
  await ensureSchema();

  const record = {
    id: randomUUID(),
    name: payload.name,
    company: payload.company,
    telegramOrEmail: payload.telegram_or_email,
    projectSummary: payload.project_summary,
    budgetRange: payload.budget_range || "Нужно обсудить",
    consent: String(payload.consent),
    source,
    ipHash,
    createdAt: new Date().toISOString(),
  };

  await db.insert(leads).values(record);
  return record;
}

export async function listLeads() {
  await ensureSchema();
  return db.select().from(leads).orderBy(desc(leads.createdAt));
}

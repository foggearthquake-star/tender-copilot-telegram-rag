import { sql } from "drizzle-orm";
import { sqliteTable, text } from "drizzle-orm/sqlite-core";

export const leads = sqliteTable("leads", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  company: text("company").notNull(),
  telegramOrEmail: text("telegram_or_email").notNull(),
  projectSummary: text("project_summary").notNull(),
  budgetRange: text("budget_range").notNull(),
  consent: text("consent").notNull().default("true"),
  source: text("source").notNull(),
  ipHash: text("ip_hash").notNull(),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

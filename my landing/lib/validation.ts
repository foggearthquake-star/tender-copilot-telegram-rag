import { z } from "zod";

const contactRegex =
  /^(?:@?[a-zA-Z0-9_]{5,}|[^\s@]+@[^\s@]+\.[^\s@]+|(?:\+?\d[\d\s\-()]{8,}\d))$/;

export const leadSchema = z.object({
  name: z.string().trim().min(2).max(80),
  company: z.string().trim().min(2).max(120),
  telegram_or_email: z.string().trim().min(5).max(120).regex(contactRegex),
  project_summary: z.string().trim().min(20).max(2400),
  budget_range: z.string().trim().max(60).optional().default("Нужно обсудить"),
  consent: z.literal(true),
  website: z.string().max(0).optional().default(""),
});

export type LeadInput = z.infer<typeof leadSchema>;

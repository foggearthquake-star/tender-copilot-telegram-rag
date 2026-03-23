export type LeadFormPayload = {
  name: string;
  company: string;
  telegram_or_email: string;
  project_summary: string;
  budget_range?: string;
  consent: boolean;
  website?: string;
};

export type LeadRecord = LeadFormPayload & {
  id: string;
  created_at: string;
  source: string;
  ip_hash: string;
};

export type LeadApiStatus = "success" | "validation_error" | "throttled" | "delivery_error";

export type LeadApiResponse = {
  status: LeadApiStatus;
  message: string;
};

export type CaseStudyTeaser = {
  eyebrow: string;
  title: string;
  problem: string;
  solution: string;
  result: string;
  stack: string[];
};

export type CapabilityItem = {
  id: string;
  title: string;
  description: string;
};

export type ProcessStep = {
  index: string;
  title: string;
  description: string;
};

export type CollaborationMode = {
  title: string;
  description: string;
  note: string;
};

export type FaqItem = {
  question: string;
  answer: string;
};

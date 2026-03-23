"use client";

import { startTransition, useState, useTransition } from "react";

import { budgetOptions } from "@/lib/site-data";
import type { LeadApiResponse, LeadFormPayload } from "@/lib/types";

const initialState: LeadFormPayload = {
  name: "",
  company: "",
  telegram_or_email: "",
  project_summary: "",
  budget_range: "Нужно обсудить",
  consent: false,
  website: "",
};

export default function LeadForm() {
  const [form, setForm] = useState<LeadFormPayload>(initialState);
  const [response, setResponse] = useState<LeadApiResponse | null>(null);
  const [isPending, startRequest] = useTransition();

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResponse(null);

    startRequest(async () => {
      const result = await fetch("/api/leads", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      const payload = (await result.json()) as LeadApiResponse;

      startTransition(() => {
        setResponse(payload);
        if (payload.status === "success") {
          setForm(initialState);
        }
      });
    });
  };

  return (
    <form className="lead-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <label>
          <span>Имя</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            name="name"
            placeholder="Как к тебе обращаться"
            required
          />
        </label>
        <label>
          <span>Компания</span>
          <input
            value={form.company}
            onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))}
            name="company"
            placeholder="Название компании"
            required
          />
        </label>
        <label>
          <span>Telegram или email</span>
          <input
            value={form.telegram_or_email}
            onChange={(event) => setForm((current) => ({ ...current, telegram_or_email: event.target.value }))}
            name="telegram_or_email"
            placeholder="@username или почта"
            required
          />
        </label>
        <label>
          <span>Бюджет</span>
          <select
            value={form.budget_range}
            onChange={(event) => setForm((current) => ({ ...current, budget_range: event.target.value }))}
            name="budget_range"
          >
            {budgetOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="summary-field">
        <span>Что нужно собрать или автоматизировать</span>
        <textarea
          value={form.project_summary}
          onChange={(event) => setForm((current) => ({ ...current, project_summary: event.target.value }))}
          name="project_summary"
          placeholder="Коротко опиши задачу, текущий процесс и желаемый результат."
          rows={6}
          required
        />
      </label>

      <div className="hp-field" aria-hidden="true">
        <label>
          <span>Website</span>
          <input
            tabIndex={-1}
            autoComplete="off"
            value={form.website}
            onChange={(event) => setForm((current) => ({ ...current, website: event.target.value }))}
            name="website"
          />
        </label>
      </div>

      <label className="consent-row">
        <input
          type="checkbox"
          checked={form.consent}
          onChange={(event) => setForm((current) => ({ ...current, consent: event.target.checked }))}
          name="consent"
          required
        />
        <span>Согласен на обработку контакта и описания задачи для ответа по проекту.</span>
      </label>

      <div className="form-actions">
        <button className="button button-dark" type="submit" disabled={isPending}>
          {isPending ? "Отправляю..." : "Отправить заявку"}
        </button>
        <a className="button button-light" href="https://t.me/nurevergarden" target="_blank" rel="noreferrer">
          Написать сразу в Telegram
        </a>
      </div>

      {response ? <p className={`form-response is-${response.status}`}>{response.message}</p> : null}
    </form>
  );
}

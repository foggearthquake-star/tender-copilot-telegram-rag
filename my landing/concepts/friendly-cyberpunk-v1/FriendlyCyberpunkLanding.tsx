import Image from "next/image";

import LeadForm from "@/app/LeadForm";

import styles from "./friendly-cyberpunk-v1.module.css";

const softSignals = [
  "Интеграция под ключ, а не набор разовых трюков",
  "Автоматизация, которая снимает ручную нагрузку",
  "Оптимизация процессов с живым сопровождением",
];

const serviceCards = [
  {
    title: "AI-ассистенты и рабочие интерфейсы",
    text: "Собираю интерфейсы, где AI помогает человеку идти по задаче, а не мешает лишним шумом и магией ради магии.",
  },
  {
    title: "RAG, знания и объяснимые ответы",
    text: "Подключаю документы, правила, знания компании и retrieval так, чтобы ответ системы был понятным, проверяемым и полезным.",
  },
  {
    title: "Интеграции и backend-логика",
    text: "Связываю LLM, CRM, Telegram, базы данных, внутренние сервисы и API в единый рабочий контур.",
  },
  {
    title: "Поддержка после запуска",
    text: "После запуска остаюсь в контуре: правки, новые сценарии, усиление логики, доп. автоматизация и развитие системы.",
  },
];

const proofItems = [
  {
    title: "Системы, которые не прячут логику",
    text: "Мне важно, чтобы AI не выглядел как чёрный ящик. Поэтому в решениях есть структура, evidence, fallback и контроль качества.",
  },
  {
    title: "Продукты, а не набор случайных промптов",
    text: "Я думаю не отдельными запросами, а сценарием: вход, обработка, решение, сохранение результата и следующий шаг.",
  },
  {
    title: "Развитие, а не одноразовая демонстрация",
    text: "Если система пошла в работу, она должна уметь расти. Под это закладываются нормальный backend и понятный слой изменений.",
  },
];

const workSteps = [
  "Сначала разбираем задачу и сам процесс, а не выбираем модную модель.",
  "Потом я собираю архитектуру: интерфейс, данные, интеграции, роли AI и точки контроля.",
  "Дальше появляется рабочая версия, которую уже можно тестировать на реальном сценарии.",
  "После запуска систему можно перевести в поддержку, оптимизацию или развивать отдельными итерациями.",
];

const faqItems = [
  {
    question: "Ты делаешь только чат-ботов?",
    answer:
      "Нет. Чат может быть частью решения, но обычно я собираю полноценный контур: интерфейс, backend, знания, сценарии и интеграции.",
  },
  {
    question: "Можно ли начать с одной задачи?",
    answer:
      "Да. Это нормальный путь. Берём один процесс, проверяем полезность, собираем первую рабочую версию и уже потом масштабируем.",
  },
  {
    question: "Что будет после релиза?",
    answer:
      "После запуска можно перейти в формат сопровождения: правки, новые сценарии, подключение новых источников данных и развитие логики.",
  },
];

export default function FriendlyCyberpunkLanding() {
  return (
    <main className={styles.scene}>
      <div className={styles.noise} />
      <header className={styles.header}>
        <a className={styles.brand} href="#top">
          <span className={styles.brandMain}>AINUR</span>
          <span className={styles.brandSub}>AI atelier for business systems</span>
        </a>
        <nav className={styles.nav}>
          <a href="#services">Что делаю</a>
          <a href="#proof">Почему мне можно доверять</a>
          <a href="#process">Как я работаю</a>
          <a href="#contact">Контакт</a>
        </nav>
        <a className={styles.telegramButton} href="https://t.me/nurevergarden" target="_blank" rel="noreferrer">
          Telegram
        </a>
      </header>

      <section className={styles.hero} id="top">
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>Fantasy tech, kind interface, serious engineering</p>
          <h1>
            Собираю AI-системы под ключ, которые автоматизируют рутину, усиливают процессы и ощущаются как живой умный
            инструмент, а не холодная машина.
          </h1>
          <p className={styles.heroText}>
            Я беру на себя интеграцию под ключ: разбираю задачу, собираю архитектуру, связываю интерфейс, данные,
            автоматизацию и backend-логику, а затем довожу систему до реального использования и следующего этапа роста.
          </p>
          <div className={styles.heroActions}>
            <a className={styles.primaryButton} href="#contact">
              Обсудить проект
            </a>
            <a className={styles.secondaryButton} href="https://t.me/nurevergarden" target="_blank" rel="noreferrer">
              Написать в Telegram
            </a>
          </div>
          <div className={styles.signalGrid}>
            {softSignals.map((item) => (
              <div key={item} className={styles.signalCard}>
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className={styles.heroVisual}>
          <div className={styles.avatarWrap}>
            <div className={styles.pixelTag}>AI GUIDE</div>
            <div className={styles.glowRune} />
            <Image
              src="/character-main.png"
              alt="Дружелюбный sci-fi персонаж Ainur"
              width={960}
              height={960}
              className={styles.avatar}
              priority
            />
          </div>
          <div className={styles.moonWrap}>
            <Image src="/logo-main.png" alt="Логотип Ainur" width={420} height={420} className={styles.moon} />
          </div>
        </div>
      </section>

      <section className={styles.ribbon}>
        <div>
          <span>anime-inspired interface</span>
          <span>soft green glow</span>
          <span>pixel details</span>
          <span>AI systems with backbone</span>
          <span>friendly cyberpunk</span>
        </div>
      </section>

      <section className={styles.block} id="services">
        <div className={styles.blockHeader}>
          <p className={styles.kicker}>Что я делаю</p>
          <h2>Я не продаю “AI вообще”. Я собираю конкретные системы, которые берут на себя часть реальной работы и делают процесс легче.</h2>
        </div>
        <div className={styles.serviceGrid}>
          {serviceCards.map((item, index) => (
            <article key={item.title} className={styles.serviceCard}>
              <span>0{index + 1}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.block} id="proof">
        <div className={styles.blockHeader}>
          <p className={styles.kicker}>Почему это не просто красивая картинка</p>
          <h2>Под мягким визуалом здесь всё равно лежат инженерная дисциплина, структура, контроль и понятная логика.</h2>
        </div>
        <div className={styles.proofGrid}>
          {proofItems.map((item) => (
            <article key={item.title} className={styles.proofCard}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.block} id="process">
        <div className={styles.blockHeader}>
          <p className={styles.kicker}>Как я работаю</p>
          <h2>Сначала смысл и задача. Потом архитектура. Потом рабочая версия. И только после этого поддержка, развитие и оптимизация.</h2>
        </div>
        <div className={styles.processGrid}>
          {workSteps.map((step, index) => (
            <article key={step} className={styles.processCard}>
              <span>0{index + 1}</span>
              <p>{step}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.block}>
        <div className={styles.blockHeader}>
          <p className={styles.kicker}>FAQ</p>
          <h2>Чтобы не тратить первый разговор на базовые вопросы, закрываю их сразу здесь.</h2>
        </div>
        <div className={styles.faqStack}>
          {faqItems.map((item) => (
            <details key={item.question} className={styles.faqItem}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section className={styles.contactBlock} id="contact">
        <div className={styles.contactCopy}>
          <p className={styles.kicker}>Контакт</p>
          <h2>Если хочешь пересобрать процесс с помощью AI, начни с короткого описания задачи и желаемого результата.</h2>
          <p>
            Самый быстрый путь это Telegram:{" "}
            <a href="https://t.me/nurevergarden" target="_blank" rel="noreferrer">
              @nurevergarden
            </a>
            . Если удобнее, оставь заявку в форме.
          </p>
          <p className={styles.contactHint}>
            Беру проекты на внедрение под ключ, автоматизацию, оптимизацию и сопровождение после запуска.
          </p>
        </div>
        <div className={styles.formWrap}>
          <LeadForm />
        </div>
      </section>
    </main>
  );
}

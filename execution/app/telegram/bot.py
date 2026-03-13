from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, KeyboardButton, Message, ReplyKeyboardMarkup

from app.core.config import settings
from app.schemas.models import CompanyProfile
from app.schemas.session import SessionState
from app.services.llm_service import LLMService
from app.services.parsers import parse_document
from app.services.pipeline import TenderPipeline
from app.services.profile_from_doc import build_profile_from_company_text
from app.storage.factory import build_repository
from app.storage.session_store import SessionStore

PROFILE_STEPS = [
    "company_name",
    "categories",
    "regions",
    "max_contract_value_rub",
    "min_margin_percent",
    "required_certificates",
    "stop_factors",
]

PROFILE_PROMPTS = {
    "company_name": "Шаг 1/7. Название компании:",
    "categories": "Шаг 2/7. Категории (через запятую), например: it, интеграция, разработка",
    "regions": "Шаг 3/7. Регионы работы (через запятую), например: Россия, Москва",
    "max_contract_value_rub": "Шаг 4/7. Максимальная сумма контракта (RUB), только число:",
    "min_margin_percent": "Шаг 5/7. Минимальная маржа (%), только число:",
    "required_certificates": "Шаг 6/7. Обязательные сертификаты/лицензии (через запятую) или '-' если нет",
    "stop_factors": "Шаг 7/7. Стоп-факторы (через запятую) или '-' если нет",
}

BTN_SETUP = "Настроить компанию"
BTN_SETUP_DOC = "Профиль файлом"
BTN_NEW_TENDER = "Новый тендер"
BTN_READY_TENDER = "Готово, анализировать"
BTN_DECISION = "Показать решение"
BTN_BID_DRAFT = "Черновик заявки"
BTN_EVIDENCE = "Доказательства"
BTN_REPORT = "Скачать PDF отчет"
BTN_EXPORT_JSON = "Скачать JSON"
BTN_STATUS = "Статус"
BTN_RUNS = "История запусков"
BTN_HELP = "Помощь"
BTN_CANCEL = "Отмена"

BUTTON_TO_COMMAND = {
    BTN_SETUP: "company_setup",
    BTN_SETUP_DOC: "company_doc",
    BTN_NEW_TENDER: "new_tender",
    BTN_DECISION: "decision",
    BTN_BID_DRAFT: "bid_draft",
    BTN_EVIDENCE: "evidence",
    BTN_REPORT: "report",
    BTN_EXPORT_JSON: "export_json",
    BTN_STATUS: "status",
    BTN_RUNS: "runs",
    BTN_HELP: "help",
    BTN_CANCEL: "cancel",
}


class TenderBotApp:
    def __init__(self) -> None:
        self.repo = build_repository()
        self.pipeline = TenderPipeline()
        self.llm_service = LLMService()
        self.dp = Dispatcher()
        self.session_store = SessionStore(settings.redis_url)

        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_health, Command("health"))
        self.dp.message.register(self.cmd_runs, Command("runs"))
        self.dp.message.register(self.cmd_cancel, Command("cancel"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_company_setup, Command("company_setup"))
        self.dp.message.register(self.cmd_company_doc, Command("company_doc"))
        self.dp.message.register(self.cmd_new_tender, Command("new_tender"))
        self.dp.message.register(self.cmd_decision, Command("decision"))
        self.dp.message.register(self.cmd_evidence, Command("evidence"))
        self.dp.message.register(self.cmd_bid_draft, Command("bid_draft"))
        self.dp.message.register(self.cmd_export_json, Command("export_json"))
        self.dp.message.register(self.cmd_report, Command("report"))
        self.dp.message.register(self.handle_document, F.document)
        self.dp.message.register(self.handle_text)

    def _session(self, user_id: int) -> SessionState:
        return self.session_store.get(user_id)

    def _save_session(self, user_id: int, session: SessionState) -> None:
        self.session_store.save(user_id, session)

    def _reset_session(self, user_id: int) -> None:
        self.session_store.clear(user_id)

    def _analysis_ready(self, user_id: int) -> bool:
        run = self.repo.get_last_tender_run(user_id)
        return bool(run and run.decision)

    def _menu_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        session = self._session(user_id)
        profile = self.repo.get_profile(user_id)
        has_analysis = self._analysis_ready(user_id)
        has_runs = self.repo.get_last_tender_run(user_id) is not None

        if session.mode == "upload_tender":
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=BTN_READY_TENDER)],
                    [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_CANCEL)],
                    [KeyboardButton(text=BTN_HELP)],
                ],
                resize_keyboard=True,
                input_field_placeholder="Загрузите документы и нажмите «Готово, анализировать»",
            )

        if session.mode != "idle":
            keyboard = [
                [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_CANCEL)],
                [KeyboardButton(text=BTN_HELP)],
            ]
            if has_runs:
                keyboard.append([KeyboardButton(text=BTN_RUNS)])
            return ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                input_field_placeholder="Идет сценарий. Завершите шаг или нажмите «Отмена».",
            )

        if not profile:
            keyboard = [
                [KeyboardButton(text=BTN_SETUP), KeyboardButton(text=BTN_SETUP_DOC)],
                [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_HELP)],
            ]
            return ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                input_field_placeholder="Начните с настройки профиля компании",
            )

        if profile and not has_analysis:
            keyboard = [
                [KeyboardButton(text=BTN_NEW_TENDER)],
                [KeyboardButton(text=BTN_SETUP), KeyboardButton(text=BTN_SETUP_DOC)],
                [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_RUNS)],
                [KeyboardButton(text=BTN_HELP)],
            ]
            return ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                input_field_placeholder="Следующий шаг: загрузите документы по тендеру",
            )

        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=BTN_NEW_TENDER), KeyboardButton(text=BTN_DECISION)],
                [KeyboardButton(text=BTN_EVIDENCE), KeyboardButton(text=BTN_BID_DRAFT)],
                [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_EXPORT_JSON)],
                [KeyboardButton(text=BTN_SETUP), KeyboardButton(text=BTN_SETUP_DOC)],
                [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_RUNS)],
                [KeyboardButton(text=BTN_HELP), KeyboardButton(text=BTN_CANCEL)],
            ],
            resize_keyboard=True,
            input_field_placeholder="Анализ готов. Выберите следующий шаг.",
        )
    def _status_ru(self, status_code: str) -> str:
        mapping = {
            "GO": "ПОДАВАТЬСЯ",
            "REVIEW": "ПРОВЕРИТЬ ВРУЧНУЮ",
            "NO_GO": "НЕ ПОДАВАТЬСЯ",
        }
        return mapping.get(status_code, status_code)

    async def cmd_start(self, message: Message) -> None:
        await message.answer(
            "Tender Copilot помогает сопоставить документы тендера с профилем вашей компании и быстро понять, стоит ли участвовать.\n\n"
            "Что делает бот:\n"
            "- принимает один или несколько PDF/DOCX по тендеру\n"
            "- принимает отдельный файл о компании и извлекает из него опыт, специализацию и ограничения\n"
            "- выдает решение: ПОДАВАТЬСЯ / ПРОВЕРИТЬ ВРУЧНУЮ / НЕ ПОДАВАТЬСЯ\n"
            "- показывает доказательства из тендерных документов и профиля компании\n"
            "- формирует черновик заявки, а если вы приложили свой черновик, использует его как основу\n"
            "- отдает PDF-отчет для людей и JSON для интеграций\n\n"
            "Как работать:\n"
            "1. Настройте профиль компании вручную или загрузите файл о компании.\n"
            "2. Загрузите документы тендера. Можно загрузить несколько файлов.\n"
            "3. Запустите анализ.\n"
            "4. После анализа откроются решение, доказательства, черновик заявки и экспорты.\n\n"
            "Что значат экспорты:\n"
            "- PDF-отчет: итоговый документ для руководителя, коллеги или внутреннего согласования.\n"
            "- JSON: технический формат для CRM, таблиц, BI и других интеграций.",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )

    async def cmd_help(self, message: Message) -> None:
        await message.answer(
            "Порядок работы:\n\n"
            "1. Настроить компанию\n"
            "Заполните профиль вручную или через файл о компании. Чем подробнее профиль, тем точнее решение и черновик заявки.\n\n"
            "2. Новый тендер\n"
            "Загрузите один или несколько PDF/DOCX. Если у вас уже есть свой черновик заявки, загрузите его вместе с остальными файлами. Затем нажмите «Готово, анализировать».\n\n"
            "3. Показать решение\n"
            "Вы получите итоговый статус и 4 интерпретируемые метрики:\n"
            "- соответствие компании тендеру\n"
            "- полнота извлеченных данных\n"
            "- качество доказательств\n"
            "- риск участия\n\n"
            "4. Доказательства\n"
            "Показывают реальные фрагменты из файлов, на которых основано решение.\n\n"
            "5. Черновик заявки\n"
            "Если был приложен ваш черновик, бот опирается на него. Если нет, строит шаблон и подсказывает, чего не хватает.\n\n"
            "6. Экспорты\n"
            "- PDF: читаемый итоговый отчет\n"
            "- JSON: техническая выгрузка для систем",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )

    async def cmd_company_doc(self, message: Message) -> None:
        session = self._session(message.from_user.id)
        session.mode = "upload_company_doc"
        self._save_session(message.from_user.id, session)
        await message.answer(
            "Загрузите PDF/DOCX с профилем компании.\n"
            "Чем полезнее документ, тем лучше бот поймет вашу специализацию. Желательно, чтобы там были:\n"
            "1) чем занимается компания\n"
            "2) проекты и кейсы\n"
            "3) узкие специализации\n"
            "4) регионы работы\n"
            "5) ограничения по бюджету, марже, оплате\n"
            "6) лицензии, сертификаты, СРО\n"
            "7) состав команды, ключевые компетенции, стек\n\n"
            "После загрузки бот извлечет профиль и будет использовать его как контекст для RAG и черновика заявки.",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )

    async def cmd_health(self, message: Message) -> None:
        storage_exists = Path(settings.storage_path).exists()
        uploads_exists = Path(settings.upload_dir).exists()
        reports_exists = Path(settings.reports_dir).exists()
        audit_exists = Path(settings.audit_log_path).exists()
        llm_state = "api" if self.llm_service.enabled else "heuristic"
        vector_effective = self.pipeline.vector_service.backend
        await message.answer(
            "Health check:\n"
            f"- storage: {'ok' if storage_exists else 'missing'}\n"
            f"- uploads_dir: {'ok' if uploads_exists else 'missing'}\n"
            f"- reports_dir: {'ok' if reports_exists else 'missing'}\n"
            f"- audit_log: {'ok' if audit_exists else 'missing'} ({settings.audit_log_path})\n"
            f"- llm_mode: {llm_state}\n"
            f"- vector_backend(config): {settings.vector_backend}\n"
            f"- vector_backend(effective): {vector_effective}",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )

    async def cmd_cancel(self, message: Message) -> None:
        session = self._session(message.from_user.id)
        self._reset_session(message.from_user.id)
        if session.mode != "idle":
            await message.answer("Текущий сценарий сброшен.", reply_markup=self._menu_keyboard(message.from_user.id))
        else:
            await message.answer("Нет активного сценария.", reply_markup=self._menu_keyboard(message.from_user.id))

    async def cmd_status(self, message: Message) -> None:
        user_id = message.from_user.id
        session = self._session(user_id)
        run = self.repo.get_last_tender_run(user_id)
        if run:
            last_stage_error = "нет"
            failed = [s for s in run.stages if s.status == "failed" and s.error]
            if failed:
                last_stage_error = failed[-1].error or "unknown"
            await message.answer(
                f"Текущий режим: {session.mode}\n"
                f"run_id: {run.run_id or '-'}\n"
                f"Последний tender_id: {run.tender_input.tender_id}\n"
                f"Pipeline status: {run.status}\n"
                f"stages: {len(run.stages)}\n"
                f"duration: {run.total_duration_ms or 0} ms\n"
                f"warnings: {len(run.warnings)}\n"
                f"last_error: {last_stage_error}\n"
                + ("Подсказка: чтобы продолжить анализ, нажмите «Готово, анализировать»." if session.mode == "upload_tender" else ""),
                reply_markup=self._menu_keyboard(message.from_user.id),
            )
            return
        await message.answer(f"Текущий режим: {session.mode}. Анализов пока нет.", reply_markup=self._menu_keyboard(message.from_user.id))

    async def cmd_runs(self, message: Message) -> None:
        runs = self.repo.get_recent_tender_runs(message.from_user.id, limit=5)
        if not runs:
            await message.answer("История запусков пуста. Сначала выполните «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        lines: list[str] = []
        for idx, run in enumerate(runs, start=1):
            lines.append(
                f"{idx}) tender_id={run.tender_input.tender_id}, status={run.status}, "
                f"duration={run.total_duration_ms or 0}ms, stages={len(run.stages)}"
            )
        await message.answer("Последние запуски:\n" + "\n".join(lines), reply_markup=self._menu_keyboard(message.from_user.id))

    async def cmd_company_setup(self, message: Message) -> None:
        session = self._session(message.from_user.id)
        session.mode = "company_setup"
        session.profile_step_index = 0
        session.draft_profile = {}
        self._save_session(message.from_user.id, session)
        step_key = PROFILE_STEPS[0]
        await message.answer("Запускаю мастер профиля компании.", reply_markup=self._menu_keyboard(message.from_user.id))
        await message.answer(PROFILE_PROMPTS[step_key])

    async def cmd_new_tender(self, message: Message) -> None:
        profile = self.repo.get_profile(message.from_user.id)
        if not profile:
            await message.answer("Сначала выполните шаг «Настроить компанию».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        session = self._session(message.from_user.id)
        session.mode = "upload_tender"
        session.pending_files.clear()
        session.tender_meta_deadline = None
        session.tender_meta_price_hint = None
        session.tender_meta_comment = None
        self._save_session(message.from_user.id, session)
        await message.answer("Отправьте один или несколько PDF/DOCX по тендеру. Если у вас уже есть свой черновик заявки, приложите его вместе с документами. После загрузки нажмите «Готово, анализировать».", reply_markup=self._menu_keyboard(message.from_user.id))

    async def handle_document(self, message: Message, bot: Bot) -> None:
        user_id = message.from_user.id
        session = self._session(user_id)
        if session.mode not in {"upload_tender", "upload_company_doc"}:
            return

        ext = Path(message.document.file_name).suffix.lower()
        if ext not in {".pdf", ".docx"}:
            await message.answer("Поддерживаются только PDF и DOCX")
            return

        file = await bot.get_file(message.document.file_id)
        file_name = f"{user_id}_{message.document.file_unique_id}{ext}"
        dest = Path(settings.upload_dir) / file_name
        await bot.download_file(file.file_path, destination=dest)
        session.pending_files.append(str(dest))
        self._save_session(user_id, session)
        await message.answer(f"Файл принят: {message.document.file_name}")

        if session.mode == "upload_company_doc":
            try:
                parsed = parse_document(dest)
                profile = build_profile_from_company_text(parsed.text)
                self.repo.save_profile(user_id, profile)
                session.mode = "idle"
                session.pending_files.clear()
                self._save_session(user_id, session)
                await message.answer(
                    "Профиль компании создан из файла:\n"
                    f"- Название: {profile.company_name}\n"
                    f"- Категории: {', '.join(profile.categories) if profile.categories else 'не определены'}\n"
                    f"- Регионы: {', '.join(profile.regions) if profile.regions else 'не определены'}\n"
                    f"- Лимит контракта: {int(profile.max_contract_value_rub):,} RUB\n"
                    f"- Мин. маржа: {profile.min_margin_percent}%\n\n"
                    "При необходимости можете уточнить профиль через «Настроить компанию».",
                    reply_markup=self._menu_keyboard(user_id),
                )
            except Exception as exc:
                await message.answer(
                    f"Не удалось обработать профиль из файла: {exc}\n"
                    "Попробуйте другой файл или заполните через «Настроить компанию».",
                    reply_markup=self._menu_keyboard(user_id),
                )

    def _parse_list(self, text: str) -> list[str]:
        if text.strip() == "-":
            return []
        return [x.strip() for x in text.split(",") if x.strip()]

    async def _handle_company_setup_text(self, message: Message, session: SessionState, text: str) -> bool:
        step_key = PROFILE_STEPS[session.profile_step_index]
        try:
            if step_key in {"company_name"}:
                if not text:
                    raise ValueError("Поле не может быть пустым")
                session.draft_profile[step_key] = text
            elif step_key in {"categories", "regions", "required_certificates", "stop_factors"}:
                session.draft_profile[step_key] = self._parse_list(text)
            elif step_key in {"max_contract_value_rub", "min_margin_percent"}:
                session.draft_profile[step_key] = float(text.replace(" ", ""))
            else:
                raise ValueError("Неизвестный шаг")
        except ValueError as exc:
            await message.answer(f"Ошибка ввода: {exc}. Повторите шаг.")
            await message.answer(PROFILE_PROMPTS[step_key])
            return True

        session.profile_step_index += 1
        self._save_session(message.from_user.id, session)
        if session.profile_step_index >= len(PROFILE_STEPS):
            profile = CompanyProfile(**session.draft_profile)
            self.repo.save_profile(message.from_user.id, profile)
            session.mode = "idle"
            self._save_session(message.from_user.id, session)
            await message.answer("Профиль сохранен. Теперь нажмите «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return True

        next_step_key = PROFILE_STEPS[session.profile_step_index]
        await message.answer(PROFILE_PROMPTS[next_step_key])
        return True

    async def _handle_tender_meta(self, message: Message, session: SessionState, text: str) -> bool:
        profile = self.repo.get_profile(message.from_user.id)
        if not profile:
            session.mode = "idle"
            await message.answer("Сначала заполните профиль компании.")
            return True

        if session.mode == "tender_meta_deadline":
            session.tender_meta_deadline = None if text == "-" else text
            session.mode = "tender_meta_price"
            self._save_session(message.from_user.id, session)
            await message.answer("Введите ориентир по сумме тендера в RUB или '-' если неизвестно")
            return True

        if session.mode == "tender_meta_price":
            if text == "-":
                session.tender_meta_price_hint = None
            else:
                try:
                    session.tender_meta_price_hint = float(text.replace(" ", ""))
                except ValueError:
                    await message.answer("Нужно число или '-'. Повторите ввод суммы")
                    return True
            session.mode = "tender_meta_comment"
            self._save_session(message.from_user.id, session)
            await message.answer("Комментарий к тендеру или '-' если нет")
            return True

        if session.mode == "tender_meta_comment":
            session.tender_meta_comment = None if text == "-" else text
            await message.answer("Запускаю анализ документов...")
            run = self.pipeline.run(
                profile=profile,
                files=session.pending_files,
                deadline=session.tender_meta_deadline,
                price_hint_rub=session.tender_meta_price_hint,
                comment=session.tender_meta_comment,
            )
            self.repo.save_tender_run(message.from_user.id, run)
            session.mode = "idle"
            self._save_session(message.from_user.id, session)
            warning_text = ""
            if run.warnings:
                human_warnings: list[str] = []
                if any(w.startswith("ocr_used:") for w in run.warnings):
                    human_warnings.append("Для части PDF был использован OCR.")
                if any(w.startswith("empty_text_extraction:") for w in run.warnings):
                    human_warnings.append("Часть файлов дала мало текста; качество решения может быть ниже.")
                if human_warnings:
                    warning_text = "\n\nПримечание: " + " ".join(human_warnings)
            await message.answer(
                f"Анализ завершен. Статус: {self._status_ru(run.decision.status.value)} ({run.decision.status.value}).\n"
                "Теперь доступны: «Показать решение», «Доказательства», «Черновик заявки», «Скачать PDF отчет»."
                + warning_text,
                reply_markup=self._menu_keyboard(message.from_user.id),
            )
            return True

        return False

    async def handle_text(self, message: Message) -> None:
        user_id = message.from_user.id
        session = self._session(user_id)
        text = (message.text or "").strip()

        if text in BUTTON_TO_COMMAND:
            command = BUTTON_TO_COMMAND[text]
            allowed_during_flow = {"help", "cancel", "status", "runs"}
            if session.mode != "idle" and command not in allowed_during_flow:
                await message.answer(
                    "Сначала завершите текущий шаг или нажмите «Отмена».",
                    reply_markup=self._menu_keyboard(message.from_user.id),
                )
                return
            command_handler = getattr(self, f"cmd_{command}", None)
            if command_handler:
                await command_handler(message)
                return

        if session.mode == "company_setup":
            handled = await self._handle_company_setup_text(message, session, text)
            if handled:
                return

        if session.mode == "upload_tender" and text.upper() == "ГОТОВО":
            if not session.pending_files:
                await message.answer("Нет загруженных файлов. Отправьте документы перед ГОТОВО.")
                return
            session.mode = "tender_meta_deadline"
            self._save_session(message.from_user.id, session)
            await message.answer("Введите дедлайн (ДД.ММ.ГГГГ или YYYY-MM-DD) или '-' если неизвестно")
            return

        if session.mode == "upload_tender" and text == BTN_READY_TENDER:
            if not session.pending_files:
                await message.answer("Сначала загрузите хотя бы один PDF/DOCX, затем нажмите «Готово, анализировать».", reply_markup=self._menu_keyboard(message.from_user.id))
                return
            session.mode = "tender_meta_deadline"
            self._save_session(message.from_user.id, session)
            await message.answer("Введите дедлайн (ДД.ММ.ГГГГ или YYYY-MM-DD) или '-' если неизвестно")
            return

        if session.mode in {"tender_meta_deadline", "tender_meta_price", "tender_meta_comment"}:
            handled = await self._handle_tender_meta(message, session, text)
            if handled:
                return

    async def cmd_decision(self, message: Message) -> None:
        if not self._analysis_ready(message.from_user.id):
            await message.answer("Решение пока недоступно. Сначала выполните «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        run = self.repo.get_last_tender_run(message.from_user.id)
        if not run or not run.decision:
            await message.answer("Нет данных по последнему тендеру. Сначала выполните «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        d = run.decision
        status_ru = self._status_ru(d.status.value)
        evidence_lines: list[str] = []
        for ev in d.evidence[:3]:
            quote = (ev.quote or "").strip().replace("\n", " ")
            if len(quote) > 160:
                quote = quote[:160] + "..."
            source_label = "профиль компании" if ev.doc_name.startswith("company_profile") else "тендерный документ"
            evidence_lines.append(f"- {source_label}: [{ev.doc_name} | {ev.fragment_ref}] {quote}")
        evidence_text = "\n".join(evidence_lines) if evidence_lines else "- подтверждающие фрагменты не найдены"

        reasons_text = "\n- ".join(d.reasons) if d.reasons else "нет"
        risks_text = "\n- ".join(d.risks) if d.risks else "нет"
        next_actions_text = "\n- ".join(d.next_actions) if d.next_actions else "нет"

        text = (
            f"Статус: {status_ru} ({d.status.value})\n"
            f"Итоговый балл: {d.overall_score}/100\n"
            f"Уверенность: {d.confidence} ({d.confidence_reason})\n\n"
            "Субметрики:\n"
            f"- Соответствие компании тендеру: {d.fit_score}/100\n"
            f"- Полнота извлеченных данных: {d.completeness_score}/100\n"
            f"- Качество доказательств: {d.evidence_score}/100\n"
            f"- Риск участия: {d.risk_score}/100\n\n"
            "Причины:\n- " + reasons_text + "\n"
            "Риски:\n- " + risks_text + "\n"
            "Доказательства (top-3):\n" + evidence_text + "\n"
            "Что делать дальше:\n- " + next_actions_text + "\n"
            f"Метрики исполнения: latency={d.latency_ms}ms, cost_estimate={d.cost_estimate_rub} RUB"
        )
        if run.warnings and any(w.startswith("empty_text_extraction") for w in run.warnings):
            text += "\n\nВажно: часть PDF не удалось прочитать как обычный текст. Для них использован OCR или требуется более качественный исходный файл."
        await message.answer(text, reply_markup=self._menu_keyboard(message.from_user.id))

    async def cmd_bid_draft(self, message: Message) -> None:
        if not self._analysis_ready(message.from_user.id):
            await message.answer("Черновик пока недоступен. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        run = self.repo.get_last_tender_run(message.from_user.id)
        if not run or not run.bid_outline:
            await message.answer("Нет черновика. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        b = run.bid_outline
        required = "\n- ".join(b.required_sections) if b.required_sections else "нет"
        recommended = "\n- ".join(b.recommended_sections) if b.recommended_sections else "нет"
        missing = "\n- ".join(b.missing_information) if b.missing_information else "нет"
        checklist = "\n- ".join(b.submission_checklist) if b.submission_checklist else "нет"
        await message.answer(
            f"{b.title}\n"
            "Обязательные разделы:\n- "
            + required
            + "\nРекомендуемые:\n- "
            + recommended
            + "\nЧто нужно дозапросить:\n- "
            + missing
            + "\nЧеклист подачи:\n- "
            + checklist,
            reply_markup=self._menu_keyboard(message.from_user.id),
        )

    async def cmd_evidence(self, message: Message) -> None:
        if not self._analysis_ready(message.from_user.id):
            await message.answer("Доказательства пока недоступны. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        run = self.repo.get_last_tender_run(message.from_user.id)
        if not run or not run.decision:
            await message.answer("Нет данных по доказательствам. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        evidence = run.decision.evidence
        if not evidence:
            await message.answer("Доказательства не найдены для последнего анализа.", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        lines = []
        for idx, ev in enumerate(evidence[:8], start=1):
            quote = (ev.quote or "").strip().replace("\n", " ")
            if len(quote) > 260:
                quote = quote[:260] + "..."
            source_label = "профиль компании" if ev.doc_name.startswith("company_profile") else "тендерный документ"
            lines.append(
                f"{idx}) Источник: {source_label}\n"
                f"Файл: {ev.doc_name}\n"
                f"Фрагмент: {ev.fragment_ref}\n"
                f"Релевантность: {ev.relevance}\n"
                f"Цитата: {quote}"
            )
        await message.answer("Доказательства из документов:\n\n" + "\n\n".join(lines), reply_markup=self._menu_keyboard(message.from_user.id))

    async def cmd_export_json(self, message: Message) -> None:
        if not self._analysis_ready(message.from_user.id):
            await message.answer("JSON-экспорт недоступен. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        run = self.repo.get_last_tender_run(message.from_user.id)
        if not run:
            await message.answer("Нет данных для экспорта. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return

        export_dir = Path(settings.reports_dir)
        export_path = export_dir / f"export_{run.tender_input.tender_id}.json"
        payload = {
            "schema_version": "1.1.0",
            "exported_at": datetime.now(UTC).isoformat(),
            "data": run.model_dump(mode="json"),
        }
        export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        await message.answer(
            "JSON-экспорт готов.\n"
            "Для обычного пользователя он не обязателен.\n"
            "Он нужен, когда нужно автоматически загрузить результат в CRM, таблицы или другую систему.",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )
        await message.answer_document(FSInputFile(export_path.as_posix()))

    async def cmd_report(self, message: Message) -> None:
        if not self._analysis_ready(message.from_user.id):
            await message.answer("PDF-отчет недоступен. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        run = self.repo.get_last_tender_run(message.from_user.id)
        if not run or not run.report_path:
            await message.answer("Отчет отсутствует. Сначала выполните шаг «Новый тендер».", reply_markup=self._menu_keyboard(message.from_user.id))
            return
        if run.decision:
            top_risks = run.decision.risks[:3] if run.decision.risks else ["нет критичных рисков"]
            await message.answer(
                "Резюме перед PDF:\n"
                f"- статус: {self._status_ru(run.decision.status.value)} ({run.decision.status.value})\n"
                f"- итоговый балл: {run.decision.overall_score}/100\n"
                f"- уверенность: {run.decision.confidence}\n"
                "- top risks:\n- " + "\n- ".join(top_risks)
            )
        await message.answer(
            "PDF-отчет — это удобный итоговый файл для людей:\n"
            "можно отправить руководителю, коллеге или приложить к внутреннему согласованию.",
            reply_markup=self._menu_keyboard(message.from_user.id),
        )
        path = Path(run.report_path)
        if not path.exists():
            await message.answer("Отчет не найден на диске")
            return
        await message.answer_document(FSInputFile(path.as_posix()))

    async def run(self) -> None:
        token = settings.telegram_bot_token
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")
        bot = Bot(token=token)
        await self.dp.start_polling(bot)














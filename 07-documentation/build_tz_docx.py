# -*- coding: utf-8 -*-
"""Build Q Premium TZ DOCX from TZ01.txt with images."""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = Path(__file__).parent
ASSETS = Path(__file__).resolve().parents[3] / ".cursor" / "projects" / "c-Users-Desktop-ALIHAN-AI-OFFICE" / "assets"
# fallback path
if not ASSETS.exists():
    ASSETS = Path(r"C:\Users\Алихан\.cursor\projects\c-Users-Desktop-ALIHAN-AI-OFFICE\assets")

OUTPUT = BASE / "Q-Premium-TZ-v1.3.docx"

WINE = RGBColor(0x72, 0x2F, 0x37)
GOLD = RGBColor(0xC9, 0xA9, 0x62)
DARK = RGBColor(0x2C, 0x2C, 0x2C)
GRAY = RGBColor(0x66, 0x66, 0x66)


def setup_styles(doc):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = DARK
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    for level, size in [(1, 18), (2, 14), (3, 12)]:
        name = f"Heading {level}"
        h = doc.styles[name]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = WINE
        h.paragraph_format.space_before = Pt(18 if level == 1 else 12)
        h.paragraph_format.space_after = Pt(8)


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = " PAGE "
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run.font.size = Pt(9)
    run.font.color.rgb = GRAY


def add_cover(doc, cover_path):
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    if cover_path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(cover_path), width=Inches(6.0))

    doc.add_page_break()


def add_meta_block(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ТЕХНИЧЕСКОЕ ЗАДАНИЕ")
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = WINE

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Система лояльности Q Premium")
    r2.font.size = Pt(16)
    r2.font.color.rgb = DARK

    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    meta = [
        ("Проект", "Q Premium — сеть магазинов одежды"),
        ("Версия документа", "1.3"),
        ("Дата", "02.09.2026"),
        ("Заказчик", "Q Premium"),
        ("Исполнитель", "ALIHAN AI OFFICE"),
    ]
    for i, (k, v) in enumerate(meta):
        table.rows[i].cells[0].text = k
        table.rows[i].cells[1].text = v
        for cell in table.rows[i].cells:
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(2)
                for run in para.runs:
                    run.font.size = Pt(10)

    doc.add_paragraph()
    doc.add_heading("Содержание", level=1)
    toc_items = [
        "1. Цель проекта",
        "2. Общая схема системы",
        "3. Пользовательские роли",
        "4. Авторизация и определение роли",
        "5. Регистрация клиента",
        "6. Единая база клиентов",
        "7. Данные клиента",
        "8–11. Клиентский Mini App",
        "12–18. Правила начисления и списания баллов",
        "19–25. Операции кассира",
        "26–35. Административная панель",
        "36–39. Операции и история",
        "40–48. Технический стек и архитектура",
        "49–54. Инфраструктура и безопасность",
        "55–60. Уведомления, логика и результат v1",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item, style="List Bullet")
        p.paragraph_format.left_indent = Cm(0.5)

    doc.add_page_break()


def add_image(doc, path, caption=None, width=5.8):
    if path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(path), width=Inches(width))
        if caption:
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in cap.runs:
                run.font.size = Pt(9)
                run.font.italic = True
                run.font.color.rgb = GRAY
        doc.add_paragraph()


def bullet_list(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def code_block(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.font.color.rgb = DARK


def build_document():
    doc = Document()
    setup_styles(doc)
    add_page_number(doc.sections[0])

    add_cover(doc, ASSETS / "q-premium-cover.png")
    add_meta_block(doc)

    # --- 1 ---
    doc.add_heading("1. Цель проекта", level=1)
    doc.add_paragraph(
        "Разработать единую систему лояльности для сети из 4 магазинов одежды Q Premium."
    )
    doc.add_paragraph("Система должна позволять:")
    bullet_list(doc, [
        "регистрировать клиентов;",
        "хранить единую базу клиентов;",
        "начислять и списывать бонусные баллы;",
        "разделять накопительные и подарочные баллы;",
        "показывать клиенту текущий баланс;",
        "отправлять клиентам текстовые сообщения через Telegram;",
        "позволять кассирам создавать операции с баллами;",
        "передавать начисления на подтверждение администратору;",
        "вести историю всех операций внутри системы;",
        "предоставлять администратору статистику;",
        "управлять правилами программы лояльности;",
        "в дальнейшем подключить собственную систему учёта и продаж.",
    ])
    doc.add_paragraph(
        "На первом этапе система лояльности является самостоятельной системой. "
        "В дальнейшем она должна иметь возможность интеграции с собственной системой учёта и кассой."
    )

    # --- 2 ---
    doc.add_heading("2. Общая схема системы", level=1)
    doc.add_paragraph(
        "Система работает внутри Telegram. Основной интерфейс клиента и администратора — Telegram Mini App."
    )
    add_image(doc, ASSETS / "q-premium-architecture.png", "Рис. 1 — Общая архитектура системы Q Premium")
    doc.add_paragraph("Кассир и администратор также работают через Telegram.")

    # --- 3 ---
    doc.add_heading("3. Пользовательские роли", level=1)
    doc.add_paragraph("В системе предусмотрено 3 роли:")

    doc.add_heading("Клиент", level=2)
    doc.add_paragraph("Может:")
    bullet_list(doc, [
        "зарегистрироваться;",
        "посмотреть текущий баланс;",
        "посмотреть свои данные;",
        "изменить свои данные;",
        "посмотреть правила программы;",
        "получать сообщения и информацию об акциях.",
    ])

    doc.add_heading("Кассир (доступ магазина)", level=2)
    doc.add_paragraph(
        "Каждый магазин сети имеет свой доступ в системе. К магазину привязываются Telegram ID "
        "сотрудников, которые работают на этой точке."
    )
    doc.add_paragraph(
        "Единая база клиентов (раздел 6) и доступы магазинов — разные вещи: клиенты одни на всю сеть; "
        "кассиры входят через Telegram ID, привязанный к конкретному магазину. "
        "Личный именованный аккаунт не создаётся — администратор указывает Telegram ID и привязывает его к магазину. "
        "На один магазин можно привязать несколько Telegram ID; один Telegram ID — только к одному магазину."
    )
    doc.add_paragraph("Кассир может:")
    bullet_list(doc, [
        "найти клиента;",
        "посмотреть текущий баланс клиента;",
        "создать операцию начисления;",
        "создать операцию списания;",
        "видеть результат созданной операции.",
    ])
    doc.add_paragraph("Кассир не имеет доступа к административным функциям.")
    doc.add_paragraph(
        "При создании операции система сохраняет идентификатор магазина и Telegram ID, "
        "с которого выполнена операция."
    )

    doc.add_heading("Администратор", level=2)
    doc.add_paragraph("Имеет полный доступ к системе:")
    bullet_list(doc, [
        "клиенты;", "операции;", "подтверждение начислений;", "баллы;",
        "кассиры;", "настройки;", "статистика;", "рассылки.",
    ])

    # --- 4 ---
    doc.add_heading("4. Авторизация и определение роли", level=1)
    doc.add_paragraph(
        "Авторизация пользователей осуществляется через Telegram. "
        "У каждого пользователя определяется Telegram ID. Backend проверяет, какая роль закреплена за данным Telegram ID."
    )
    code_block(doc, "Telegram ID → роль\n123456789 → STORE (Магазин 1)\n234567890 → STORE (Магазин 2)\n987654321 → ADMIN")
    doc.add_paragraph(
        "Backend определяет не только роль, но и магазин, если роль — STORE."
    )
    doc.add_paragraph(
        "После авторизации система автоматически показывает интерфейс, соответствующий роли."
    )
    doc.add_paragraph(
        "Важно: роль проверяется на backend, а не только на уровне отображения кнопок. "
        "Даже если пользователь попытается напрямую отправить запрос к административному API, "
        "backend должен проверить его права и отказать в доступе при отсутствии необходимых разрешений."
    )

    # --- 5 ---
    doc.add_heading("5. Регистрация клиента", level=1)
    doc.add_paragraph("В магазинах Q Premium размещается QR-код. Клиент сканирует QR-код и переходит в Telegram-бот.")
    add_image(doc, ASSETS / "q-premium-registration.png", "Рис. 2 — Сценарий регистрации клиента")
    doc.add_paragraph("Клиент заполняет:")
    bullet_list(doc, ["ФИО;", "номер телефона;", "email;", "дату рождения."])
    doc.add_paragraph(
        "Перед регистрацией клиенту отображаются условия программы лояльности и необходимые согласия. "
        "После завершения регистрации клиент становится участником программы лояльности и создаётся в общей базе."
    )

    # --- 6-7 ---
    doc.add_heading("6. Единая база клиентов", level=1)
    doc.add_paragraph(
        "Все 4 магазина Q Premium работают с одной общей базой клиентов. "
        "Отдельных баз для каждого магазина не создаётся. "
        "Клиент регистрируется один раз и после этого может совершать покупки в любом из 4 магазинов. "
        "Все операции с его бонусами работают с единым балансом."
    )

    doc.add_heading("7. Данные клиента", level=1)
    doc.add_paragraph("В карточке клиента хранятся:")
    bullet_list(doc, [
        "внутренний ID;", "Telegram ID;", "ФИО;", "номер телефона;", "email;", "дата рождения;",
        "дата регистрации;", "накопительные баллы;", "подарочные баллы;",
        "общее количество баллов;", "общая сумма покупок;", "количество операций;",
        "статус клиента;", "дата последней операции.",
    ])
    doc.add_paragraph(
        "Также в базе сохраняется история всех операций клиента. "
        "История используется системой и доступна администратору."
    )

    # --- 8-11 ---
    doc.add_heading("8. Клиентский Mini App", level=1)
    doc.add_paragraph(
        "Mini App открывается непосредственно внутри Telegram. Отдельное приложение скачивать не требуется."
    )
    doc.add_heading("Мой баланс", level=2)
    code_block(doc, (
        "Накопительные баллы: 2 500\n"
        "  └ Сгорят 15.10.2026: 800\n"
        "  └ Сгорят 01.12.2026: 1 700\n\n"
        "Подарочные баллы: 500\n"
        "  └ Сгорят 20.09.2026: 500\n\n"
        "Всего: 3 000 баллов\n\n"
        "Ближайшие сгорания:\n"
        "  20.09.2026 — 500 подарочных\n"
        "  15.10.2026 — 800 накопительных"
    ))
    doc.add_paragraph(
        "Накопительные и подарочные баллы отображаются отдельно. "
        "Для каждого типа показывается баланс и даты сгорания ближайших партий баллов. "
        "Клиент не видит историю операций."
    )

    doc.add_heading("9. Мои данные", level=1)
    doc.add_paragraph(
        "Клиент может посмотреть и редактировать свои данные (ФИО, телефон, email, дата рождения). "
        "После изменения информация обновляется в общей базе клиентов."
    )

    doc.add_heading("10. Правила программы", level=1)
    doc.add_paragraph("Клиент может посмотреть актуальные правила программы лояльности:")
    bullet_list(doc, [
        "сколько процентов начисляется за покупку;",
        "сколько составляет 1 балл;",
        "срок действия накопительных баллов;",
        "срок действия подарочных баллов;",
        "максимальный процент оплаты покупки баллами;",
        "другие условия программы.",
    ])
    doc.add_paragraph(
        "Числовые параметры подтягиваются из настроек автоматически. "
        "Поясняющий текст правил администратор редактирует вручную в админке."
    )

    doc.add_heading("11. Акции", level=1)
    doc.add_paragraph(
        "В Mini App клиент может видеть информацию об актуальных акциях магазина. "
        "На первом этапе предусматривается простое отображение текстовой информации об акциях."
    )

    # --- 12-18 ---
    doc.add_heading("12. Накопительные баллы", level=1)
    code_block(doc, "Покупка: 10 000 ₽\nПроцент начисления: 5%\nНачисляется: 500 баллов")
    doc.add_paragraph(
        "Количество баллов рассчитывается системой автоматически. "
        "Кассир не вводит количество баллов вручную."
    )

    doc.add_heading("13. Порог начисления", level=1)
    doc.add_paragraph(
        "В административных настройках предусматривается параметр: "
        "«Минимальная сумма покупки для начисления баллов». "
        "Если сумма покупки меньше установленного значения, баллы не начисляются."
    )

    doc.add_heading("14. Процент начисления", level=1)
    doc.add_paragraph("Администратор может самостоятельно установить процент начисления.")
    code_block(doc, "10 000 ₽ × 5% = 500 баллов\n10 000 ₽ × 10% = 1 000 баллов")
    doc.add_paragraph("Изменение настройки не требует изменения программного кода.")

    doc.add_heading("15. Срок действия накопительных баллов", level=1)
    doc.add_paragraph(
        "Администратор устанавливает срок действия накопительных баллов (например, 3 месяца). "
        "После окончания срока неиспользованные баллы становятся недействительными. "
        "Система фиксирует факт сгорания баллов в истории операций."
    )

    doc.add_heading("16. Подарочные баллы", level=1)
    doc.add_paragraph("Подарочные баллы являются отдельным типом баллов и не смешиваются с накопительными.")
    doc.add_paragraph("Подарочные баллы могут использоваться:")
    bullet_list(doc, [
        "за регистрацию;", "в качестве подарка;", "в рамках акции;",
        "в качестве персонального бонуса;", "на день рождения.",
    ])

    doc.add_heading("17. Срок действия подарочных баллов", level=1)
    doc.add_paragraph(
        "Для подарочных баллов устанавливается отдельный срок действия (например, 30 дней). "
        "Срок устанавливается администратором."
    )

    doc.add_heading("18. Максимальное списание баллов", level=1)
    doc.add_paragraph(
        "Администратор устанавливает максимальный процент покупки, который можно оплатить баллами."
    )
    code_block(doc, "Покупка: 10 000 ₽\nМаксимальное списание: 30%\nМаксимум: 3 000 баллов")
    doc.add_paragraph(
        "Система автоматически рассчитывает допустимый лимит. "
        "Кассир не сможет провести списание выше установленного ограничения."
    )

    # --- 19-25 ---
    doc.add_heading("19. Начисление баллов кассиром", level=1)
    doc.add_paragraph(
        "Кассир работает через Telegram ID, привязанный к своему магазину (см. раздел 30)."
    )
    add_image(doc, ASSETS / "q-premium-cashier-flow.png", "Рис. 3 — Процесс начисления баллов кассиром")
    steps = [
        "Кассир нажимает «Начислить баллы».",
        "Вводит номер телефона клиента.",
        "Система находит клиента.",
        "Кассир вводит сумму покупки (например, 10 000 ₽).",
        "Система автоматически рассчитывает количество баллов (10 000 × 5% = 500).",
        "Операция отправляется администратору на подтверждение.",
    ]
    for i, s in enumerate(steps, 1):
        doc.add_paragraph(f"Шаг {i}. {s}")

    doc.add_heading("20. Подтверждение начисления администратором", level=1)
    doc.add_paragraph(
        "Начисление не зачисляется клиенту сразу. После создания операции она получает статус PENDING (ожидает подтверждения)."
    )
    code_block(doc, (
        "Клиент: Иван Иванов\nТелефон: +7...\nДата: 22.08.2026  Время: 14:35\n"
        "Сумма покупки: 10 000 ₽\nНачислено: 500 баллов\n"
        "Магазин: Магазин 1 (ул. Примерная, 10)\n"
        "Telegram ID оператора: 123456789\n"
        "Статус: Ожидает подтверждения"
    ))
    doc.add_paragraph("Администратор может:")
    bullet_list(doc, [
        "Подтвердить — операция получает статус CONFIRMED, баллы зачисляются клиенту.",
        "Отклонить — операция получает статус REJECTED, баллы клиенту не начисляются.",
    ])

    doc.add_heading("21. Список операций на подтверждение", level=1)
    doc.add_paragraph(
        "В административной панели создаётся отдельный раздел «Ожидают подтверждения». "
        "Если администратор не заходит каждый день, операции продолжают накапливаться."
    )

    doc.add_heading("22. Данные операции", level=1)
    doc.add_paragraph("Для каждой операции отображаются:")
    bullet_list(doc, [
        "дата;", "время;", "клиент;", "номер телефона;",
        "сумма покупки;", "количество начисляемых баллов;",
        "тип баллов;", "магазин (источник операции);",
        "Telegram ID оператора;", "статус операции.",
    ])

    doc.add_heading("23. Редактирование операции администратором", level=1)
    doc.add_paragraph(
        "До подтверждения администратор может изменить сумму покупки и количество начисляемых баллов. "
        "При изменении суммы система автоматически пересчитывает количество баллов."
    )
    code_block(doc, "Было: 10 000 ₽ → 500 баллов\nИзменено: 8 000 ₽ → 400 баллов")

    doc.add_heading("24. Списание баллов", level=1)
    doc.add_paragraph("Кассир может создать операцию списания баллов. Сценарий:")
    bullet_list(doc, [
        "найти клиента (по телефону);",
        "выбрать «Списать баллы»;",
        "указать сумму покупки;",
        "система автоматически рассчитывает максимально допустимое списание, доступный баланс и итог по FIFO;",
        "кассир не вводит количество баллов вручную — система списывает автоматически "
        "(если баллов меньше лимита — все доступные; если больше — только рассчитанный максимум);",
        "кассир подтверждает операцию; операция проводится.",
    ])
    doc.add_paragraph(
        "Перед подтверждением кассир видит preview: сумма покупки, сколько будет списано, остаток баллов."
    )
    doc.add_paragraph("Система проверяет: наличие баллов, доступный баланс, срок действия, максимальный процент оплаты и другие ограничения.")

    doc.add_heading("25. Порядок использования баллов", level=1)
    doc.add_paragraph(
        "При списании используется правило FIFO по сроку жизни: сначала списываются "
        "баллы, у которых срок действия заканчивается раньше."
    )

    doc.add_heading("26. Административная панель", level=1)
    doc.add_paragraph("Административная панель реализуется как Telegram Mini App.")
    code_block(doc, (
        "Главная | Клиенты | Операции | Ожидают подтверждения\n"
        "Баллы | Кассиры | Статистика | Рассылки | Настройки\n"
        "  ├── Правила программы\n"
        "  ├── Администраторы\n"
        "  └── Резервная копия"
    ))
    doc.add_paragraph(
        "В разделе «Настройки» (или отдельном подразделе) администратор может скачать "
        "резервную копию базы данных — см. раздел 53."
    )

    doc.add_heading("27. Раздел «Клиенты»", level=1)
    bullet_list(doc, [
        "посмотреть список клиентов;", "найти клиента;", "открыть карточку клиента;",
        "посмотреть баланс и данные;", "посмотреть историю операций;",
        "начислить подарочные баллы;", "выполнить корректировку;",
        "выгрузить список клиентов (кнопка «Выгрузить» / «Скачать список»).",
    ])

    doc.add_heading("28. Поиск клиентов", level=1)
    doc.add_paragraph("Поиск по ФИО и номеру телефона. Фильтры: сумма покупок, количество покупок, количество баллов.")

    doc.add_heading("29. История операций для администратора", level=1)
    doc.add_paragraph("Администратор имеет доступ к полной истории: начисления, списания, подарочные баллы, сгорание, корректировки, отменённые операции.")

    doc.add_heading("30. Магазины и доступы кассиров", level=1)
    doc.add_paragraph(
        "В системе ведётся справочник магазинов. По умолчанию — 4 магазина; администратор может добавлять новые."
    )
    doc.add_paragraph(
        "В разделе «Магазины» (или «Кассиры») администратор может: создать магазин; добавить Telegram ID "
        "сотрудника и привязать его к магазину; добавить несколько Telegram ID к одному магазину; "
        "отключить доступ. Личные профили кассиров (ФИО, логин, пароль) не создаются."
    )
    doc.add_paragraph(
        "При входе кассира backend определяет магазин по Telegram ID. "
        "Если Telegram ID не привязан — доступ запрещён. "
        "Каждая операция сохраняет идентификатор и название/адрес магазина, а также Telegram ID оператора."
    )

    doc.add_heading("31. Администраторы", level=1)
    doc.add_paragraph(
        "Telegram ID связывается с ролью ADMIN. Полный доступ ко всем разделам системы."
    )
    doc.add_paragraph(
        "В разделе «Настройки → Администраторы» главный администратор может добавить нового "
        "администратора (указать Telegram ID), отключить администратора (кроме последнего активного). "
        "Минимум один активный администратор в системе должен оставаться."
    )

    doc.add_heading("32. Статистика", level=1)
    doc.add_paragraph("Периоды: неделя, месяц, год, произвольный.")
    doc.add_heading("Клиенты", level=3)
    bullet_list(doc, ["общее количество клиентов;", "новые клиенты за период."])
    doc.add_heading("Покупки", level=3)
    bullet_list(doc, ["количество операций покупок;", "общая сумма покупок."])
    doc.add_heading("Баллы", level=3)
    bullet_list(doc, [
        "начисленные накопительные;", "списанные накопительные;",
        "сгоревшие накопительные;", "выданные подарочные;",
        "использованные подарочные;", "общее количество баллов.",
    ])

    doc.add_heading("33. Рассылки", level=1)
    doc.add_paragraph(
        "Администратор может отправлять клиентам текстовые сообщения через Telegram. "
        "На первом этапе рассылки поддерживают только текстовые сообщения."
    )

    doc.add_heading("34. День рождения клиента", level=1)
    doc.add_paragraph(
        "В день рождения система автоматически начисляет подарочные баллы и отправляет "
        "поздравление в Telegram. Текст поздравления редактируется администратором в админке."
    )

    doc.add_heading("35. Настройки программы", level=1)
    code_block(doc, (
        "Процент начисления: 5%\nМаксимальное списание: 30%\n"
        "Минимальная сумма покупки: 1 000 ₽\nСрок накопительных: 3 месяца\n"
        "Баллы за регистрацию: 500\nБаллы на день рождения: 1 000\n"
        "Срок подарочных баллов: 30 дней"
    ))
    doc.add_paragraph("Администратору не требуется обращаться к разработчику для изменения этих параметров.")
    doc.add_paragraph(
        "Также в настройках (или рядом) доступна кнопка «Скачать резервную копию» — "
        "администратор получает файл backup на свой компьютер."
    )

    # --- 36-39 ---
    doc.add_heading("36. История операций", level=1)
    doc.add_paragraph("Основные типы операций:")
    code_block(doc, "BONUS_ACCRUAL | BONUS_REDEMPTION | GIFT_ACCRUAL\nBONUS_EXPIRATION | MANUAL_ADJUSTMENT")
    doc.add_paragraph("Для каждой операции сохраняются: ID, клиент, тип, сумма, баллы, тип баллов, дата, время, статус, комментарий, источник.")

    doc.add_heading("37. Статусы операций", level=1)
    code_block(doc, "PENDING → CONFIRMED\nPENDING → REJECTED\nСтатусы: PENDING | CONFIRMED | REJECTED | CANCELLED")
    doc.add_paragraph("Операции не удаляются из базы после завершения.")

    doc.add_heading("38. Защита от повторного начисления", level=1)
    doc.add_paragraph("Используются: уникальный ID операции, проверка статуса, транзакции БД, защита от повторной обработки запроса.")

    doc.add_heading("39. Корректировка баллов", level=1)
    doc.add_paragraph(
        "Баланс нельзя менять напрямую без сохранения причины. "
        "Создаётся отдельная операция корректировки с сохранением истории."
    )

    # --- 40-48 ---
    doc.add_heading("40. Технический стек", level=1)
    table = doc.add_table(rows=6, cols=2)
    table.style = "Table Grid"
    stack = [
        ("Backend", "Python 3.x, Django, Django REST Framework"),
        ("База данных", "PostgreSQL"),
        ("Telegram Bot", "aiogram"),
        ("Mini App Frontend", "Vue 3, TypeScript, Vite, Quasar"),
        ("Сервер", "Ubuntu Server LTS, Docker, Nginx"),
        ("Фоновые задачи", "Redis, Celery (при необходимости)"),
    ]
    for i, (k, v) in enumerate(stack):
        table.rows[i].cells[0].text = k
        table.rows[i].cells[1].text = v

    doc.add_heading("41. База данных", level=1)
    doc.add_paragraph("Основные сущности:")
    code_block(doc, "User | Role | Store | StoreAccess | Client | BonusBalance | BonusTransaction\nPurchase | ProgramSettings | Broadcast | AdminUser")

    doc.add_heading("42. Telegram Bot", level=1)
    doc.add_paragraph("Бот отвечает за: запуск, регистрацию, меню, взаимодействие, отправку сообщений, открытие Mini App, работу кассира.")

    doc.add_heading("43. Mini App", level=1)
    doc.add_paragraph(
        "Mini App отвечает за интерфейсы клиента, администратора и кассира: "
        "таблицы, формы, поиск, настройки, статистику, отображение баланса."
    )

    doc.add_heading("44. Архитектура frontend/backend", level=1)
    add_image(doc, ASSETS / "q-premium-tech-stack.png", "Рис. 4 — Архитектура frontend/backend и будущая интеграция")
    doc.add_paragraph("Frontend не имеет прямого доступа к базе данных. Все операции проходят через backend.")

    doc.add_heading("45. Авторизация Mini App", level=1)
    doc.add_paragraph(
        "При запуске Mini App Telegram передаёт данные пользователя. "
        "Backend самостоятельно проверяет подлинность. "
        "Нельзя доверять Telegram ID, переданному frontend без проверки."
    )
    code_block(doc, "Telegram ID → поиск пользователя → определение роли → проверка разрешений → доступ")

    doc.add_heading("46. Разграничение доступа", level=1)
    doc.add_paragraph("Роли: CLIENT, STORE, ADMIN.")
    code_block(doc, (
        "Клиент: GET /api/profile, GET /api/balance\n"
        "Кассир (STORE): GET /api/clients, POST /api/accruals, POST /api/redemptions\n"
        "Администратор: полный доступ, включая магазины, кассиров и администраторов"
    ))

    doc.add_heading("47. API", level=1)
    code_block(doc, (
        "/api/auth/ | /api/users/ | /api/stores/ | /api/store-access/ | /api/admins/\n"
        "/api/clients/ | /api/balances/ | /api/accruals/ | /api/redemptions/\n"
        "/api/transactions/ | /api/statistics/ | /api/settings/ | /api/broadcasts/"
    ))

    doc.add_heading("48. Архитектура для будущей системы учёта", level=1)
    doc.add_paragraph(
        "Система лояльности отделена от способа регистрации покупки. "
        "Сейчас: Кассир → Сумма покупки → Система лояльности. "
        "В будущем: Система продаж → API → Bonus Engine → расчёт баллов. "
        "Логика расчёта бонусов остаётся единой."
    )

    # --- 49-54 ---
    doc.add_heading("49. Сервер", level=1)
    doc.add_paragraph(
        "Ubuntu Server LTS на VPS/облачном сервере. "
        "Компоненты: backend, PostgreSQL, Nginx, Telegram webhook, Mini App frontend, фоновые сервисы."
    )

    doc.add_heading("50. Docker", level=1)
    code_block(doc, "Docker\n├── Backend\n├── PostgreSQL\n├── Nginx\n└── Worker")
    doc.add_paragraph("Redis и Celery — для рассылок, сгорания баллов, отложенных операций.")

    doc.add_heading("51. HTTPS", level=1)
    doc.add_paragraph("Все внешние соединения через HTTPS. Mini App только через защищённое соединение.")

    doc.add_heading("52. Безопасность", level=1)
    bullet_list(doc, [
        "HTTPS;", "безопасное хранение секретных ключей;", "переменные окружения;",
        "отсутствие секретов в Git;", "проверка Telegram авторизации;",
        "разграничение ролей;", "проверка прав на backend;",
        "валидация входящих данных;", "защита от повторного выполнения операций;",
        "логирование важных действий;", "резервное копирование БД;",
        "ограничение доступа к серверу.",
    ])

    doc.add_heading("53. Резервное копирование базы данных", level=1)
    doc.add_paragraph(
        "Резервное копирование PostgreSQL выполняется автоматически на VPS."
    )
    doc.add_heading("Автоматическое резервное копирование", level=2)
    doc.add_paragraph(
        "Система каждый день (1 раз в сутки) автоматически создаёт резервную копию "
        "базы данных на сервере (VPS)."
    )
    code_block(doc, "PostgreSQL → Backup → backup_2026-08-22.sql.gz")
    doc.add_paragraph(
        "Файл содержит данные базы в формате, из которого её можно восстановить. "
        "Копии сохраняются на VPS в отдельной директории."
    )
    doc.add_heading("Скачивание резервной копии администратором", level=2)
    doc.add_paragraph(
        "В административной панели предусматривается кнопка «Скачать резервную копию». "
        "При нажатии администратор получает актуальный файл резервной копии на свой компьютер."
    )
    doc.add_paragraph(
        "Отдельная сложная система автоматической передачи файлов на компьютер клиента "
        "не разрабатывается. Доступ к скачиванию имеет только администратор."
    )
    doc.add_heading("Хранение на VPS", level=2)
    code_block(doc, (
        "VPS\n"
        "  ├── backup за сегодня\n"
        "  ├── backup за вчера\n"
        "  └── backup за предыдущие дни (до 7 дней)"
    ))
    doc.add_paragraph(
        "Старые копии удаляются автоматически по истечении срока хранения. "
        "Администратор может периодически скачивать копии и сохранять их у себя локально."
    )
    doc.add_heading("Период хранения на VPS", level=2)
    bullet_list(doc, ["ежедневные копии — последние 7 дней."])
    doc.add_paragraph("Конкретный срок хранения определяется перед запуском.")
    doc.add_heading("Восстановление", level=2)
    code_block(doc, "Backup → PostgreSQL → Восстановленная база")
    doc.add_paragraph(
        "Необходимо один раз проверить, что резервная копия действительно восстанавливается. "
        "Просто наличие файлов backup не гарантирует возможность восстановления."
    )

    doc.add_heading("54. Логи", level=1)
    doc.add_paragraph("Логируются: авторизация, создание/подтверждение/отклонение операций, списание, корректировка, изменение настроек, рассылки.")

    # --- 55-60 ---
    doc.add_heading("55. Уведомления клиенту", level=1)
    bullet_list(doc, [
        "После подтверждения начисления: «Вам начислено 500 баллов 🎉»",
        "После списания: «Списано 1 000 баллов.»",
        "После отклонения: «Начисление баллов было отклонено.»",
    ])

    doc.add_heading("56. Сгорание баллов", level=1)
    doc.add_paragraph(
        "Система автоматически определяет баллы с истёкшим сроком. "
        "Факт сгорания фиксируется в истории операций."
    )

    doc.add_heading("57. Логика баллов", level=1)
    doc.add_paragraph("1 балл = 1 ₽. Накопительные и подарочные баллы учитываются отдельно.")

    doc.add_heading("58. Ограничение списания", level=1)
    code_block(doc, "Покупка: 20 000 ₽ | Макс. списание 30% = 6 000 баллов")
    doc.add_paragraph(
        "Если доступных баллов меньше лимита — система списывает все доступные. "
        "Кассир не вводит сумму списания вручную."
    )

    doc.add_heading("59. Основные пользовательские сценарии", level=1)
    add_image(doc, ASSETS / "q-premium-user-scenarios.png", "Рис. 5 — Пользовательские сценарии: Клиент, Кассир, Администратор")

    doc.add_heading("60. Результат первой версии", level=1)
    doc.add_paragraph("После реализации магазин Q Premium получает единую систему, в которой:")
    bullet_list(doc, [
        "все 4 магазина используют одну базу клиентов;",
        "регистрация через QR-код с email;",
        "клиент видит баланс с датами сгорания по каждому типу баллов;",
        "накопительные и подарочные баллы разделены;",
        "у каждого магазина свои Telegram ID кассиров (не один общий доступ);",
        "администратор добавляет магазины, привязывает Telegram ID, добавляет администраторов;",
        "на подтверждении видно магазин и Telegram ID оператора;",
        "выгрузка списка клиентов; FIFO при списании;",
        "списание баллов — автоматически, без ручного ввода суммы кассиром;",
        "авто ДР + редактируемый шаблон сообщения;",
        "ежедневный backup и кнопка «Скачать резервную копию»;",
        "архитектура позволяет подключить систему учёта и продаж.",
    ])

    doc.add_heading("61. Согласованные доработки и стоимость", level=1)
    table = doc.add_table(rows=6, cols=3)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Что меняем"
    table.rows[0].cells[1].text = "Решение"
    table.rows[0].cells[2].text = "Доплата"
    rows = [
        ("Email + выгрузка списка клиентов", "Принято", "+ 5 000 ₽"),
        ("Дата сгорания баллов в Mini App", "Принято", "без доплаты"),
        ("FIFO — списание по сроку жизни", "Принято", "+ 5 000 ₽"),
        ("Авто ДР + шаблон в админке", "Принято", "+ 15 000 ₽"),
        ("Доступ на каждый магазин + контроль операций", "Принято", "+ 20 000 ₽"),
    ]
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            table.rows[i].cells[j].text = val
    doc.add_paragraph()
    doc.add_paragraph("Доплата за доработки: 45 000 ₽")
    doc.add_paragraph("Итоговая стоимость разработки: 145 000 ₽")

    # Footer note
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("— Конец документа —")
    r.font.color.rgb = GRAY
    r.font.size = Pt(10)

    doc.save(str(OUTPUT))
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build_document()

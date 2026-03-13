from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SV_MONTHS = {
    1: "januari",
    2: "februari",
    3: "mars",
    4: "april",
    5: "maj",
    6: "juni",
    7: "juli",
    8: "augusti",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}


def fmt_day(day: date, include_year: bool = False) -> str:
    text = f"{day.day} {SV_MONTHS[day.month]}"
    if include_year:
        text += f" {day.year}"
    return text


def fmt_range(start: date, end: date) -> str:
    start_text = fmt_day(start, include_year=start.year != 2026)
    end_text = fmt_day(end, include_year=end.year != 2026)
    return f"{start_text}–{end_text}"


def easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def midsummer_day(year: int) -> date:
    for day in range(20, 27):
        candidate = date(year, 6, day)
        if candidate.weekday() == 5:
            return candidate
    raise ValueError("Could not determine Midsummer Day")


def all_saints_day(year: int) -> date:
    for month, start_day, end_day in ((10, 31, 31), (11, 1, 6)):
        for day in range(start_day, end_day + 1):
            candidate = date(year, month, day)
            if candidate.weekday() == 5:
                return candidate
    raise ValueError("Could not determine All Saints' Day")


easter = easter_sunday(2026)
OFFICIAL_HOLIDAYS = [
    ("Nyårsdagen", date(2026, 1, 1)),
    ("Trettondedag jul", date(2026, 1, 6)),
    ("Långfredag", easter - timedelta(days=2)),
    ("Påskdagen", easter),
    ("Annandag påsk", easter + timedelta(days=1)),
    ("Första maj", date(2026, 5, 1)),
    ("Kristi himmelsfärdsdag", easter + timedelta(days=39)),
    ("Pingstdagen", easter + timedelta(days=49)),
    ("Nationaldagen", date(2026, 6, 6)),
    ("Midsommardagen", midsummer_day(2026)),
    ("Alla helgons dag", all_saints_day(2026)),
    ("Juldagen", date(2026, 12, 25)),
    ("Annandag jul", date(2026, 12, 26)),
]

SCHOOL_TEXT = {
    7: "Sportlov i Västra Götalands och Jönköpings län.",
    8: "Sportlov i Uppsala, Södermanlands, Östergötlands, Örebro, Kalmar, Blekinge, Kronobergs, Skåne och Hallands län.",
    9: "Sportlov i Stockholms, Gotlands, Dalarnas, Gävleborgs, Värmlands och Västmanlands län.",
    10: "Sportlov i Norrbottens, Västerbottens, Västernorrlands och Jämtlands län.",
    14: "Påsklov i många svenska kommuner.",
    24: "Sommarlov för många elever.",
    25: "Sommarlov för många elever.",
    26: "Sommarlov för många elever.",
    27: "Sommarlov för många elever.",
    28: "Sommarlov för många elever.",
    29: "Sommarlov för många elever.",
    30: "Sommarlov för många elever.",
    31: "Sommarlov för många elever.",
    32: "Sommarlov för många elever.",
    33: "Sommarlov för många elever, medan höstterminen börjar i vissa kommuner.",
    44: "Höstlov i många svenska kommuner.",
    51: "Jullov för många elever.",
    52: "Jullov för många elever.",
    53: "Jullov för många elever.",
}


def build_description(week: int, start: date, end: date, holidays: list[str], school_text: str | None) -> str:
    parts = [f"Vecka {week} år 2026 infaller {fmt_range(start, end)}."]
    if holidays:
        parts.append(f"Röda dagar: {', '.join(holidays)}.")
    if school_text:
        parts.append(f"{school_text} Se kalender med röda dagar på VilketVeckonummer.se.")
    else:
        parts.append("Se kalender med röda dagar på VilketVeckonummer.se.")
    return " ".join(parts)


def replace_first(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Pattern not found exactly once: {pattern}")
    return updated


for week in range(1, 54):
    path = ROOT / f"vecka-{week}-2026" / "index.html"
    text = path.read_text(encoding="utf-8")
    start = date.fromisocalendar(2026, week, 1)
    end = date.fromisocalendar(2026, week, 7)
    holidays = [
        f"{name} ({fmt_day(day)})"
        for name, day in OFFICIAL_HOLIDAYS
        if start <= day <= end
    ]
    school_text = SCHOOL_TEXT.get(week)

    description = build_description(week, start, end, holidays, school_text)
    og_description = f"Vecka {week} år 2026 infaller {fmt_range(start, end)}."
    if holidays:
        og_description += f" Röda dagar: {', '.join(holidays)}."

    if holidays:
        holiday_block = "\n".join(f"        <li>{holiday}</li>" for holiday in holidays)
    else:
        holiday_block = "        <li>Inga röda dagar denna vecka.</li>"

    text = replace_first(
        text,
        r'<meta name="description" content="[^"]*" />',
        f'<meta name="description" content="{description}" />',
    )
    text = replace_first(
        text,
        r'<meta property="og:description" content="[^"]*" />',
        f'<meta property="og:description" content="{og_description}" />',
    )
    text = replace_first(
        text,
        r'("description": ")([^"]*)(",\s*\n\s*"datePublished")',
        lambda match: f'{match.group(1)}{description}{match.group(3)}',
    )
    text = replace_first(
        text,
        rf'(<h2>Röda dagar vecka {week}</h2>\s*<ul class="roda-lista">\s*)(.*?)(\s*</ul>)',
        lambda match: f'{match.group(1)}{holiday_block}{match.group(3)}',
    )

    school_pattern = rf'(<section>\s*<h2>Skollov vecka {week} 2026</h2>\s*<p>)(.*?)(</p>\s*</section>)'
    school_match = re.search(school_pattern, text, flags=re.S)
    if school_text and school_match:
        text = re.sub(school_pattern, rf'\1{school_text}\3', text, count=1, flags=re.S)
    elif school_text and not school_match:
        insert_after = '</section>\n\n    <section>\n      <h2>Relaterade sidor</h2>'
        school_section = (
            f'</section>\n\n    <section>\n'
            f'      <h2>Skollov vecka {week} 2026</h2>\n'
            f'      <p>{school_text}</p>\n'
            f'    </section>\n\n    <section>\n      <h2>Relaterade sidor</h2>'
        )
        text = replace_first(text, re.escape(insert_after), school_section)

    path.write_text(text, encoding="utf-8")
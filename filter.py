import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Резонансный фильтр", page_icon="🏡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.main-title { text-align: center; font-size: 2.8rem; font-weight: 800; background: linear-gradient(45deg, #2d3436, #0984e3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 1rem 0; }
.sub-title { text-align: center; color: #636e72; font-size: 1.1rem; margin-bottom: 2rem; }
.upload-card { background: white; border-radius: 20px; padding: 2rem 1.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.08); border: 1px solid rgba(255,255,255,0.3); transition: all 0.3s ease; height: 100%; }
.upload-card:hover { transform: translateY(-5px); box-shadow: 0 15px 50px rgba(0,0,0,0.12); }
.upload-card h3 { color: #2d3436; font-size: 1.1rem; margin-bottom: 0.5rem; }
.upload-card p { color: #b2bec3; font-size: 0.9rem; }
.result-box { background: white; border-radius: 20px; padding: 2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.08); margin-top: 2rem; }
.footer { text-align: center; color: #b2bec3; font-size: 0.8rem; margin-top: 3rem; padding: 1rem 0; border-top: 1px solid #dfe6e9; }
.badge-critical { background: #ff6b6b; color: white; padding: 0.2rem 0.8rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
.badge-high { background: #fdcb6e; color: #2d3436; padding: 0.2rem 0.8rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
.badge-medium { background: #74b9ff; color: white; padding: 0.2rem 0.8rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
.badge-low { background: #55efc4; color: #2d3436; padding: 0.2rem 0.8rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
@media (max-width: 768px) { .main-title { font-size: 2rem; } }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🏡 Резонансный фильтр</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Автоматический отбор самых опасных жалоб по дворовой территории</p>', unsafe_allow_html=True)

# ==================== ВКЛАДКИ ====================
tab1, tab2 = st.tabs(["📋 Резонансные жалобы", "🔥 Индекс социального напряжения"])

# ==================== СЛОВАРИ ОПАСНОСТЕЙ ====================
SEASON_KEYWORDS = {
    "❄️ Зима": [
        "снег", "снегопад", "сугроб", "сугробы", "не чищено", "не убран", "не почищен",
        "замело", "занесло", "снежная каша", "каток", "накат", "снег не вывезен",
        "гололед", "гололёдица", "наледь", "скользко", "поскользнулся", "поскользнулась",
        "упал на льду", "упала на льду", "лед", "обледенело", "обледенение",
        "не посыпано", "не обработано", "реагенты",
        "сосульки", "сосулька", "наледь на крыше", "лед с крыши", "глыба льда",
        "упала сосулька", "упал лед", "снег с крыши", "снег падает с крыши",
        "обвалился снег", "рухнуло на машину", "упало на машину", "упало на голову",
        "попало на машину", "попало на ребенка", "повредило машину",
        "пожилые", "пенсионеры", "бабушка", "дедушка", "мама с коляской", "коляска",
        "инвалид", "инвалидная коляска", "не могут пройти", "невозможно пройти",
        "не пройти", "не проехать", "коляска не проедет",
        "подтопление", "затопление", "заливает", "залило", "вода", "лужа",
        "прорвало", "труба лопнула", "тает снег", "таяние",
        "входная группа", "крыльцо подъезда", "вход в подъезд", "козырек подъезда",
        "крыша", "кровля", "крыша течет", "крыша протекает", "крыша обвалилась",
        "снег на крыше", "сосульки на крыше", "крыша дома",
        "яма", "выбоина", "провал", "провалился", "колесо провалилось",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе",
        "упал", "упала", "ушиб", "перелом", "синяк", "шишка", "травма",
        "растяжение", "вывих", "сотрясение", "госпитализация", "скорая", "больница"
    ],
    "🌷 Весна": [
        "подтопление", "затопление", "заливает", "залило", "лужа", "вода",
        "вода не уходит", "стоит вода", "тает", "таяние", "талая вода", "ручьи",
        "потоки воды", "вода во дворе", "вода в подвале", "подвал затопило",
        "прорвало", "труба лопнула", "ливневка", "дренаж",
        "снег", "сугроб", "сугробы", "не растаял", "остатки снега", "старый снег",
        "грязный снег", "снег не вывезен", "снежная каша", "каша", "месиво",
        "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
        "прогибается", "обломится", "качели", "горка", "карусель", "штыри",
        "проволока", "острая кромка", "сломанная площадка", "травмоопасно",
        "опасная площадка", "без бортика", "защемление", "застрял",
        "упал", "упала", "рассек", "рассекла", "поранился", "поранилась",
        "травма", "синяк", "шишка", "кровь", "скорая", "ушиб", "перелом",
        "вывих", "растяжение", "сотрясение",
        "яма", "выбоина", "провал", "провалился", "колесо провалилось",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе"
    ],
    "☀️ Лето": [
        "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
        "прогибается", "обломится", "яма", "выбоина", "провал", "упал", "рассек",
        "кровь", "скорая", "травма", "защемление", "качели", "горка", "карусель",
        "штыри", "проволока", "острая кромка", "скамья", "скамейка", "урна",
        "куча мусора", "строительный мусор", "стекло", "осколки", "опасно",
        "угроза", "угрожает", "ребенок", "дети", "малыши", "срочно", "боимся",
        "игровое оборудование", "детская площадка", "забор", "калитка", "ограждение",
        "сухостой", "аварийное дерево", "упало дерево", "ветка упала", "гнилой ствол",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе"
    ],
    "🍂 Осень": [
        "подтопление", "затопление", "заливает", "залило", "лужа", "огромная лужа",
        "гигантская лужа", "вода", "вода не уходит", "стоит вода", "ливневка",
        "ливневая канализация", "забита ливневка", "дренаж", "вода во дворе",
        "грязь", "грязно", "месиво", "невозможно пройти",
        "листва", "листья", "опавшие листья", "много листвы", "куча листьев",
        "завалило листвой", "листья не убраны", "не убирают листья",
        "скользко от листьев", "мокрые листья", "гнилые листья",
        "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
        "прогибается", "обломится", "качели", "горка", "карусель", "штыри",
        "проволока", "острая кромка", "сломанная площадка", "травмоопасно",
        "опасная площадка", "без бортика", "защемление", "застрял",
        "упал", "упала", "рассек", "рассекла", "поранился", "поранилась",
        "травма", "синяк", "шишка", "кровь", "скорая", "ушиб", "перелом",
        "вывих", "растяжение", "сотрясение",
        "яма", "выбоина", "провал", "провалился", "колесо провалилось",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе"
    ]
}

FORBIDDEN_LOCATIONS = [
    "контейнер", "контейнерная площадка", "контейнеры", "мусорные баки", "баки",
    "мусорка", "помойка", "тко", "твердые коммунальные отходы", "вывоз мусора",
    "детский сад", "детсад", "доу", "ясли", "ясельная группа",
    "школа", "школьный", "гимназия", "лицей", "учебное заведение", "образовательное учреждение",
    "больница", "поликлиника", "клиника", "стационар",
    "лифт", "лифтовое оборудование", "батарея", "отопление",
    "мусоропровод", "вентиляция",
    "проезжая часть", "трасса", "шоссе", "магистраль", "автомагистраль"
]

# ==================== СЛОВАРИ ИНДЕКСА НАПРЯЖЕНИЯ ====================
TENSION_CATEGORIES = {
    "Повторяемость": {"max": 30, "words": [
        "уже неделю", "уже месяц", "уже год", "уже полгода", "уже 2 месяца", "уже 3 месяца",
        "уже несколько месяцев", "уже несколько дней", "уже много дней", "уже 10 дней",
        "уже 5 дней", "уже 3 дня", "уже 2 дня", "уже сутки", "уже давно", "уже много лет",
        "годами", "десятилетиями", "не первый раз", "не первый год", "повторно",
        "повторная жалоба", "снова", "опять", "каждый раз", "каждый год", "каждую зиму",
        "каждое лето", "постоянно", "систематически", "регулярно", "из раза в раз",
        "из года в год", "из недели в неделю", "изо дня в день",
        "одна и та же проблема", "та же проблема", "та же история", "та же беда",
        "одно и то же", "одно и тоже", "ничего не меняется", "ничего не изменилось",
        "всё по-прежнему", "все также", "как всегда", "как обычно",
        "день", "дня", "дней", "сутки", "неделя", "недели", "недель"
    ]},
    "Бездействие": {"max": 30, "words": [
        "бездействие", "бездействуют", "игнорируют", "игнорирование", "не реагируют",
        "не отвечают", "не приходят", "не выезжают", "не делают", "ничего не делают",
        "никакой реакции", "нет реакции", "нулевая реакция", "отписка", "отписки",
        "отписались", "формальный ответ", "отговорки", "отговариваются",
        "обещали и не сделали", "обещают и не делают", "кормят завтраками",
        "тянут резину", "затягивают", "волокита", "бюрократия", "бумажная волокита",
        "жалуюсь не первый раз", "писал неоднократно", "писала неоднократно",
        "обращались много раз", "обращались неоднократно", "обращаюсь повторно",
        "уже обращались", "уже писали", "уже звонили", "никто не отвечает",
        "никто не приезжает", "никто не убирает", "никто не чинит",
        "руки не доходят", "всем всё равно", "всем наплевать", "наплевательское отношение",
        "халатность", "разгильдяйство", "бардак", "беспредел", "произвол", "самоуправство"
    ]},
    "Массовость": {"max": 20, "words": [
        "все жильцы", "все соседи", "весь дом", "весь подъезд", "весь двор",
        "вся улица", "весь район", "все жители", "весь микрорайон", "весь квартал",
        "мы всей семьей", "мы всей улицей", "мы всем домом", "мы все",
        "у всех", "у всех соседей", "у всех жильцов", "у всех такая проблема",
        "это касается всех", "страдают все", "мучаются все", "терпят все",
        "невозможно жить", "невозможно терпеть", "устали терпеть", "устали ждать",
        "устали бороться", "замучились", "задолбали", "достали", "надоело",
        "сил больше нет", "нет больше сил", "нет сил терпеть", "крайняя степень",
        "дошли до предела", "переполнилась чаша", "последняя капля",
        "критическая ситуация", "критично", "аварийная ситуация", "чп"
    ]},
    "Эмоции": {"max": 15, "words": [
        "возмутительно", "возмущение", "негодование", "вопиющий случай", "вопиющее",
        "безобразие", "беспредел", "кошмар", "ужас", "тихий ужас", "ужасно", "страшно",
        "стыдно", "позор", "позорище", "наглость", "наглые", "нахальство", "хамство",
        "хамское отношение", "неуважение", "пренебрежение", "наплевательство",
        "довели", "довели до ручки", "довели до крайности", "довели до слёз",
        "плачу", "плачем", "рыдаю", "не могу больше", "невозможно",
        "терпение лопнуло", "терпение кончилось", "лопнуло терпение"
    ]},
    "Угроза здоровью": {"max": 20, "words": [
        "опасно", "очень опасно", "угроза", "угрожает", "угроза жизни",
        "угроза здоровью", "угрожает здоровью", "опасность", "смертельная опасность",
        "травмоопасно", "травму", "травмы", "калечит", "калечат", "убивает",
        "может убить", "может травмировать", "может покалечить",
        "дети могут пострадать", "дети в опасности", "ребенок пострадал",
        "пожилые страдают", "инвалиды страдают", "беременные",
        "водители", "пешеходы", "машины", "автотранспорт"
    ]},
    "Признание без исполнения": {"max": 10, "words": [
        "признали", "признают", "согласились", "обещали", "пообещали",
        "дали обещание", "клянутся", "заверяют", "гарантируют",
        "в планах", "планируют", "обещают в этом году", "обещали к",
        "обещали сделать", "обещали исправить", "обещали решить",
        "принято решение", "решение принято", "но ничего не делается",
        "решение есть, а воз и ныне там", "дело не двигается",
        "процесс стоит", "ничего не движется", "заморозили",
        "приостановили", "отложили", "перенесли", "отложили на потом",
        "отложили на неопределенный срок", "сроки переносятся",
        "сроки сдвигаются", "сроки нарушены"
    ]},
    "Прокуратура / СМИ": {"max": 15, "words": [
        "прокуратура", "прокуратуру", "прокурор", "прокурору", "в прокуратуру",
        "пойду в прокуратуру", "обращусь в прокуратуру", "напишу в прокуратуру",
        "жалоба в прокуратуру", "надзорные органы", "надзор",
        "суд", "в суд", "подам в суд", "буду судиться", "судебный иск",
        "иск", "заявление в суд", "судебное разбирательство",
        "сми", "в сми", "средства массовой информации", "телевидение", "телеканал",
        "газета", "журналисты", "пресса", "репортаж", "сюжет",
        "расскажу в интернете", "напишу в соцсетях", "сниму видео",
        "опубликую", "огласка", "публичность", "придать огласке",
        "сделать достоянием общественности", "дойду до самого верха",
        "напишу президенту", "обращусь к губернатору", "дойду до москвы"
    ]}
}

# ==================== ФУНКЦИИ ====================
def clean_location(location):
    if not isinstance(location, str):
        return location
    cleaned = re.sub(r'\b[гм]\.о\.\s*', '', location, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\s*[гм]\.\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def calculate_score(text, keywords):
    if not isinstance(text, str):
        return 0
    text_lower = text.lower()
    for forbidden in FORBIDDEN_LOCATIONS:
        if forbidden in text_lower:
            return 0
    score = 0
    for word in keywords:
        if word in text_lower:
            score += 5
    return score

def calculate_tension(text):
    if not isinstance(text, str):
        return 0
    text_lower = text.lower()
    total = 0
    for category, data in TENSION_CATEGORIES.items():
        for word in data["words"]:
            if word in text_lower:
                total += data["max"]
                break
    return total

def format_score(score):
    if score >= 30:
        return f'<span class="badge-critical">🔴 КРИТИЧНО</span>'
    elif score >= 20:
        return f'<span class="badge-high">🟠 ВЫСОКИЙ</span>'
    elif score >= 10:
        return f'<span class="badge-medium">🟡 СРЕДНИЙ</span>'
    elif score >= 5:
        return f'<span class="badge-low">🟢 НИЗКИЙ</span>'
    return ""

def format_tension_badge(score):
    if score >= 60:
        return f'🔴 КРИТИЧЕСКИЙ'
    elif score >= 40:
        return f'🟠 ВЫСОКИЙ'
    elif score >= 25:
        return f'🟡 СРЕДНИЙ'
    elif score >= 15:
        return f'🟢 НИЗКИЙ'
    return ""

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ ====================
def load_dobrodel(file):
    """Загружает файл Добродела и оставляет только нужные столбцы"""
    df = pd.read_excel(file)
    needed = ["Номер в источнике", "ОМСУ", "Описание"]
    existing = [col for col in needed if col in df.columns]
    return df[existing].copy()

def load_incident(file):
    """Загружает файл Инцидента и оставляет только нужные столбцы"""
    df = pd.read_excel(file)
    needed = ["Номер инцидента", "Локация", "URL поста", "Контент"]
    existing = [col for col in needed if col in df.columns]
    return df[existing].copy()

# ==================== ВКЛАДКА 1: РЕЗОНАНСНЫЕ ЖАЛОБЫ ====================
with tab1:
    st.markdown("### 🗓️ Выберите сезон")
    season = st.radio(
        "",
        ["❄️ Зима", "🌷 Весна", "☀️ Лето", "🍂 Осень"],
        horizontal=True,
        label_visibility="collapsed",
        key="season_selector"
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="upload-card"><h3>📄 Файл №1 (Добродел)</h3><p>Загрузите выгрузку из Добродела</p></div>', unsafe_allow_html=True)
        file1 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_dobrodel")
    with col2:
        st.markdown('<div class="upload-card"><h3>📄 Файл №2 (Инцидент)</h3><p>Загрузите выгрузку из ЕДС</p></div>', unsafe_allow_html=True)
        file2 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_incident")

    analyze_clicked = st.button("🔍 Найти резонансные жалобы", type="primary", use_container_width=True, key="btn_resonance")

    if analyze_clicked:
        if not file1 or not file2:
            st.error("⚠️ Загрузите оба файла!")
        else:
            with st.spinner(f"🔄 Анализируем жалобы для сезона {season}..."):
                try:
                    keywords = SEASON_KEYWORDS[season]

                    df1 = load_dobrodel(file1)
                    df2 = load_incident(file2)

                    df1["Баллы"] = df1["Описание"].fillna("").apply(lambda x: calculate_score(x, keywords))
                    df1["Резонанс"] = df1["Баллы"] > 0

                    df2["Баллы"] = df2["Контент"].fillna("").apply(lambda x: calculate_score(x, keywords))
                    df2["Резонанс"] = df2["Баллы"] > 0

                    result1 = df1[df1["Резонанс"] == True].copy()
                    result2 = df2[df2["Резонанс"] == True].copy()

                    result1.drop(columns=["Резонанс"], inplace=True)
                    result2.drop(columns=["Резонанс"], inplace=True)

                    result1 = result1.drop_duplicates()
                    result2 = result2.drop_duplicates()

                    result1 = result1.sort_values("Баллы", ascending=False)
                    result2 = result2.sort_values("Баллы", ascending=False)

                    жалобы = []
                    for _, row in result1.iterrows():
                        номер = row.get("Номер в источнике", "")
                        омсу = row.get("ОМСУ", "")
                        описание = row.get("Описание", "")
                        баллы = row.get("Баллы", 0)
                        уровень = format_score(баллы)
                        жалобы.append(f"{баллы} баллов {уровень} | {номер} - {омсу} - {описание}")

                    for _, row in result2.iterrows():
                        номер = row.get("Номер инцидента", "")
                        локация = clean_location(row.get("Локация", ""))
                        контент = row.get("Контент", "")
                        url = row.get("URL поста", "")
                        баллы = row.get("Баллы", 0)
                        уровень = format_score(баллы)
                        жалобы.append(f"{баллы} баллов {уровень} | {номер} - {локация} - {контент} - {url}")

                    def extract_score(text):
                        match = re.search(r'^(\d+)', text)
                        return int(match.group(1)) if match else 0

                    жалобы = sorted(жалобы, key=extract_score, reverse=True)
                    text_output = "\n\n".join(жалобы)

                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    if not text_output:
                        st.warning(f"⚠️ Резонансных жалоб для сезона «{season}» не найдено.")
                    else:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                            <span style="font-size: 2rem;">{season.split()[0]}</span>
                            <h3 style="margin: 0; color: #2d3436;">Найдено <span style="color: #0984e3;">{len(жалобы)}</span> резонансных жалоб ({season})</h3>
                            <span style="margin-left: auto; background: #dfe6e9; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.85rem; color: #636e72;">🔽 от самых опасных</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.text_area("", text_output, height=500, label_visibility="collapsed")
                        st.download_button("📥 Скачать как .txt", data=text_output, file_name=f"резонанс_{season.split()[1].lower()}.txt", mime="text/plain")
                    st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
                    import traceback
                    st.text(traceback.format_exc())

# ==================== ВКЛАДКА 2: ИНДЕКС НАПРЯЖЕНИЯ ====================
with tab2:
    st.markdown("### 🔥 Индекс социального напряжения")
    st.markdown("""
    <div style="background: white; border-radius: 15px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <p style="color: #636e72; margin: 0;">
        Этот фильтр находит жалобы, которые сигналят о <b>системной проблеме</b>: 
        повторяемость, бездействие властей, массовость, эмоциональная накаленность, 
        угрозы здоровью и угрозы обращения в прокуратуру / СМИ.
        </p>
        <p style="color: #0984e3; margin: 0.5rem 0 0 0;"><b>Порог отбора: 15 баллов</b></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="upload-card"><h3>📄 Файл №1 (Добродел)</h3><p>Загрузите выгрузку из Добродела</p></div>', unsafe_allow_html=True)
        tension_file1 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="tension_dobrodel")
    with col2:
        st.markdown('<div class="upload-card"><h3>📄 Файл №2 (Инцидент)</h3><p>Загрузите выгрузку из ЕДС</p></div>', unsafe_allow_html=True)
        tension_file2 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="tension_incident")

    tension_clicked = st.button("🔥 Рассчитать индекс напряжения", type="primary", use_container_width=True, key="btn_tension")

    if tension_clicked:
        if not tension_file1 or not tension_file2:
            st.error("⚠️ Загрузите оба файла!")
        else:
            with st.spinner("🔄 Рассчитываем индекс социального напряжения..."):
                try:
                    df1 = load_dobrodel(tension_file1)
                    df2 = load_incident(tension_file2)

                    df1["Индекс"] = df1["Описание"].fillna("").apply(calculate_tension)
                    df2["Индекс"] = df2["Контент"].fillna("").apply(calculate_tension)

                    result1 = df1[df1["Индекс"] >= 15].copy()
                    result2 = df2[df2["Индекс"] >= 15].copy()

                    result1 = result1.drop_duplicates()
                    result2 = result2.drop_duplicates()

                    result1 = result1.sort_values("Индекс", ascending=False)
                    result2 = result2.sort_values("Индекс", ascending=False)

                    жалобы = []
                    for _, row in result1.iterrows():
                        номер = row.get("Номер в источнике", "")
                        омсу = row.get("ОМСУ", "")
                        описание = row.get("Описание", "")
                        индекс = row.get("Индекс", 0)
                        уровень = format_tension_badge(индекс)
                        жалобы.append(f"{индекс} баллов {уровень} | {номер} - {омсу} - {описание}")

                    for _, row in result2.iterrows():
                        номер = row.get("Номер инцидента", "")
                        локация = clean_location(row.get("Локация", ""))
                        контент = row.get("Контент", "")
                        url = row.get("URL поста", "")
                        индекс = row.get("Индекс", 0)
                        уровень = format_tension_badge(индекс)
                        жалобы.append(f"{индекс} баллов {уровень} | {номер} - {локация} - {контент} - {url}")

                    def extract_score(text):
                        match = re.search(r'^(\d+)', text)
                        return int(match.group(1)) if match else 0

                    жалобы = sorted(жалобы, key=extract_score, reverse=True)
                    text_output = "\n\n".join(жалобы)

                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    if not text_output:
                        st.warning("⚠️ Жалоб с высоким индексом социального напряжения не найдено.")
                    else:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                            <span style="font-size: 2rem;">🔥</span>
                            <h3 style="margin: 0; color: #2d3436;">Найдено <span style="color: #e74c3c;">{len(жалобы)}</span> жалоб с высоким напряжением</h3>
                            <span style="margin-left: auto; background: #dfe6e9; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.85rem; color: #636e72;">🔽 от самых напряжённых</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.text_area("", text_output, height=500, label_visibility="collapsed")
                        st.download_button("📥 Скачать как .txt", data=text_output, file_name="индекс_напряжения.txt", mime="text/plain")
                    st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
                    import traceback
                    st.text(traceback.format_exc())

st.markdown('<div class="footer">🏡 Резонансный фильтр • Автоматический отбор опасных жалоб по дворовой территории</div>', unsafe_allow_html=True)

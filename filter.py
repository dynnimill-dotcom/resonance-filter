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

# ==================== ВЫБОР СЕЗОНА ====================
st.markdown("### 🗓️ Выберите сезон")
season = st.radio(
    "",
    ["❄️ Зима", "🌷 Весна", "☀️ Лето", "🍂 Осень"],
    horizontal=True,
    label_visibility="collapsed"
)

# ==================== СЕЗОННЫЕ СЛОВАРИ ====================
SEASON_KEYWORDS = {
    "❄️ Зима": [
        # Снег и наледь
        "снег", "снегопад", "сугроб", "сугробы", "не чищено", "не убран", "не почищен",
        "замело", "занесло", "снежная каша", "каток", "накат", "снег не вывезен",
        # Гололёд
        "гололед", "гололёдица", "наледь", "скользко", "поскользнулся", "поскользнулась",
        "упал на льду", "упала на льду", "лед", "обледенело", "обледенение",
        "не посыпано", "не обработано", "реагенты",
        # Сосульки и падение с высоты
        "сосульки", "сосулька", "наледь на крыше", "лед с крыши", "глыба льда",
        "упала сосулька", "упал лед", "снег с крыши", "снег падает с крыши",
        "обвалился снег", "рухнуло на машину", "упало на машину", "упало на голову",
        "попало на машину", "попало на ребенка", "повредило машину",
        # Пожилые и коляски
        "пожилые", "пенсионеры", "бабушка", "дедушка", "мама с коляской", "коляска",
        "инвалид", "инвалидная коляска", "не могут пройти", "невозможно пройти",
        "не пройти", "не проехать", "коляска не проедет",
        # Подтопления
        "подтопление", "затопление", "заливает", "залило", "вода", "лужа",
        "прорвало", "труба лопнула", "тает снег", "таяние",
        # Подъезды и крыши (только зима!)
        "входная группа", "крыльцо подъезда", "вход в подъезд", "козырек подъезда",
        "крыша", "кровля", "крыша течет", "крыша протекает", "крыша обвалилась",
        "снег на крыше", "сосульки на крыше", "крыша дома",
        # Ямы и дворовые проезды
        "яма", "выбоина", "провал", "провалился", "колесо провалилось",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе",
        # Травмы
        "упал", "упала", "ушиб", "перелом", "синяк", "шишка", "травма",
        "растяжение", "вывих", "сотрясение", "госпитализация", "скорая", "больница"
    ],
    "🌷 Весна": [
        # Подтопления
        "подтопление", "затопление", "заливает", "залило", "лужа", "вода",
        "вода не уходит", "стоит вода", "тает", "таяние", "талая вода", "ручьи",
        "потоки воды", "вода во дворе", "вода в подвале", "подвал затопило",
        "прорвало", "труба лопнула", "ливневка", "дренаж",
        # Залежи снега
        "снег", "сугроб", "сугробы", "не растаял", "остатки снега", "старый снег",
        "грязный снег", "снег не вывезен", "снежная каша", "каша", "месиво",
        # Детские площадки
        "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
        "прогибается", "обломится", "качели", "горка", "карусель", "штыри",
        "проволока", "острая кромка", "сломанная площадка", "травмоопасно",
        "опасная площадка", "без бортика", "защемление", "застрял",
        # Травмы
        "упал", "упала", "рассек", "рассекла", "поранился", "поранилась",
        "травма", "синяк", "шишка", "кровь", "скорая", "ушиб", "перелом",
        "вывих", "растяжение", "сотрясение",
        # Ямы и дворовые проезды
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
        # Подтопления и лужи
        "подтопление", "затопление", "заливает", "залило", "лужа", "огромная лужа",
        "гигантская лужа", "вода", "вода не уходит", "стоит вода", "ливневка",
        "ливневая канализация", "забита ливневка", "дренаж", "вода во дворе",
        "грязь", "грязно", "месиво", "невозможно пройти",
        # Листва
        "листва", "листья", "опавшие листья", "много листвы", "куча листьев",
        "завалило листвой", "листья не убраны", "не убирают листья",
        "скользко от листьев", "мокрые листья", "гнилые листья",
        # Детские площадки
        "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
        "прогибается", "обломится", "качели", "горка", "карусель", "штыри",
        "проволока", "острая кромка", "сломанная площадка", "травмоопасно",
        "опасная площадка", "без бортика", "защемление", "застрял",
        # Травмы
        "упал", "упала", "рассек", "рассекла", "поранился", "поранилась",
        "травма", "синяк", "шишка", "кровь", "скорая", "ушиб", "перелом",
        "вывих", "растяжение", "сотрясение",
        # Ямы и дворовые проезды
        "яма", "выбоина", "провал", "провалился", "колесо провалилось",
        "бордюр разрушен", "асфальт провалился", "дворовый проезд", "проезд",
        "внутридворовый проезд", "дорога во дворе"
    ]
}

# ==================== УНИВЕРСАЛЬНЫЕ СТОП-СЛОВА (удаляем из всех сезонов) ====================
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
    
    # Проверяем стоп-слова
    for forbidden in FORBIDDEN_LOCATIONS:
        if forbidden in text_lower:
            return 0
    
    # Считаем баллы
    score = 0
    for word in keywords:
        if word in text_lower:
            score += 5
    return score

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

# ==================== ЗАГРУЗКА ФАЙЛОВ ====================
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown('<div class="upload-card"><h3>📄 Файл №1 (Добродел)</h3><p>Загрузите выгрузку из Добродела</p></div>', unsafe_allow_html=True)
    file1 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_dobrodel")
with col2:
    st.markdown('<div class="upload-card"><h3>📄 Файл №2 (Посты)</h3><p>Загрузите выгрузку из соцсетей</p></div>', unsafe_allow_html=True)
    file2 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_posts")

# ==================== АНАЛИЗ ====================
analyze_clicked = st.button("🔍 Найти резонансные жалобы", type="primary", use_container_width=True)

if analyze_clicked:
    if not file1 or not file2:
        st.error("⚠️ Загрузите оба файла!")
    else:
        with st.spinner(f"🔄 Анализируем жалобы для сезона {season}..."):
            try:
                keywords = SEASON_KEYWORDS[season]
                
                df1 = pd.read_excel(file1)
                df2 = pd.read_excel(file2)

                # Файл 1 (Добродел)
                df1["Баллы"] = df1["Описание"].fillna("").apply(lambda x: calculate_score(x, keywords))
                df1["Резонанс"] = df1["Баллы"] > 0

                # Файл 2 (Посты)
                df2["Баллы"] = df2["Контент"].fillna("").apply(lambda x: calculate_score(x, keywords))
                df2["Резонанс"] = df2["Баллы"] > 0

                result1 = df1[df1["Резонанс"] == True].copy()
                result2 = df2[df2["Резонанс"] == True].copy()

                result1.drop(columns=["Резонанс"], inplace=True)
                result2.drop(columns=["Резонанс"], inplace=True)

                result1 = result1.sort_values("Баллы", ascending=False)
                result2 = result2.sort_values("Баллы", ascending=False)

                жалобы = []
                for _, row in result1.iterrows():
                    номер = row.get("Номер в источнике", "")
                    омсу = row.get("Добродел", row.get("ОМСУ", ""))
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

st.markdown('<div class="footer">🏡 Резонансный фильтр • Автоматический отбор опасных жалоб по дворовой территории</div>', unsafe_allow_html=True)

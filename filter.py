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

with st.expander("ℹ️ Как работает система баллов", expanded=False):
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 15px;">
        <p>📊 Каждая жалоба получает баллы в зависимости от опасности:</p>
        <ul style="list-style: none; padding-left: 0;">
            <li>🔴 <b>Критично (30+ баллов)</b> — прямая угроза жизни или травма</li>
            <li>🟠 <b>Высокий (20–29 баллов)</b> — высокая вероятность травмы</li>
            <li>🟡 <b>Средний (15–19 баллов)</b> — реальная угроза</li>
            <li>🟢 <b>Низкий (10–14 баллов)</b> — потенциальная угроза</li>
        </ul>
        <p style="color: #0984e3;">✅ <b>Отбираются все жалобы с баллами 10+</b></p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown('<div class="upload-card"><h3>📄 Файл №1 (ОМСУ)</h3><p>Загрузите выгрузку из системы «Инцидент»</p></div>', unsafe_allow_html=True)
    file1 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_omsu")
with col2:
    st.markdown('<div class="upload-card"><h3>📄 Файл №2 (Посты)</h3><p>Загрузите выгрузку из «Добродела» или соцсетей</p></div>', unsafe_allow_html=True)
    file2 = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="uploader_posts")

def clean_location(location):
    if not isinstance(location, str):
        return location
    cleaned = re.sub(r'\b[гм]\.о\.\s*', '', location, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\s*[гм]\.\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

KEYWORDS = [
    "торчит", "гвоздь", "арматура", "сломана", "рухнула", "треснула", "балка",
    "прогибается", "обломится", "яма", "выбоина", "провал", "упал", "рассек",
    "кровь", "скорая", "травма", "защемление", "наледь", "гололед", "сосульки",
    "оголенный провод", "качели", "горка", "карусель", "штыри", "проволока"
]

INJURY_WORDS = [
    "упал", "упала", "рассек", "рассекла", "поранился", "поранилась", "травма",
    "синяк", "шишка", "кровь", "скорая", "защемление", "ушиб"
]

CHILD_WORDS = ["ребенок", "дети", "ребёнок", "малыши"]

URGENT_WORDS = ["опасно", "угроза", "угрожает", "срочно", "боимся"]

FORBIDDEN_LOCATIONS = [
    "подъезд", "лифт", "батарея", "мусоропровод", "контейнер",
    "крыса", "детсад", "детский сад", "школа", "больница", "поликлиника"
]

IGNORE_KEYWORDS = [
    "покрасить", "перекрасить", "эстетика", "некрасиво", "шум", "скрип",
    "парковка", "ветки мешают", "темно", "запах от мусора", "воняет"
]

def calculate_score(text):
    if not isinstance(text, str):
        return 0
    text_lower = text.lower()
    for forbidden in FORBIDDEN_LOCATIONS:
        if forbidden in text_lower:
            return 0
    for bad in IGNORE_KEYWORDS:
        if bad in text_lower:
            return 0
    score = 0
    for word in KEYWORDS:
        if word in text_lower:
            score += 10
            break
    for word in INJURY_WORDS:
        if word in text_lower:
            score += 20
            break
    for word in CHILD_WORDS:
        if word in text_lower:
            score += 10
            break
    for word in URGENT_WORDS:
        if word in text_lower:
            score += 5
            break
    return score

def is_resonant(text):
    return calculate_score(text) >= 10

def format_score(score):
    if score >= 30:
        return f'<span class="badge-critical">🔴 КРИТИЧНО</span>'
    elif score >= 20:
        return f'<span class="badge-high">🟠 ВЫСОКИЙ</span>'
    elif score >= 15:
        return f'<span class="badge-medium">🟡 СРЕДНИЙ</span>'
    elif score >= 10:
        return f'<span class="badge-low">🟢 НИЗКИЙ</span>'
    return ""

analyze_clicked = st.button("🔍 Найти резонансные жалобы", type="primary", use_container_width=True)

if analyze_clicked:
    if not file1 or not file2:
        st.error("⚠️ Загрузите оба файла!")
    else:
        with st.spinner("🔄 Анализируем жалобы..."):
            try:
                df1 = pd.read_excel(file1)
                df2 = pd.read_excel(file2)
                
                df1["Баллы"] = df1["Описание"].fillna("").apply(calculate_score)
                df1["Резонанс"] = df1["Баллы"] >= 10
                
                df2["Баллы"] = df2["Контент"].fillna("").apply(calculate_score)
                df2["Резонанс"] = df2["Баллы"] >= 10
                
                result1 = df1[df1["Резонанс"] == True].copy()
                result2 = df2[df2["Резонанс"] == True].copy()
                
                result1.drop(columns=["Резонанс"], inplace=True)
                result2.drop(columns=["Резонанс"], inplace=True)
                
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
                    st.warning("⚠️ Резонансных жалоб не найдено.")
                else:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                        <span style="font-size: 2rem;">🎯</span>
                        <h3 style="margin: 0; color: #2d3436;">Найдено <span style="color: #0984e3;">{len(жалобы)}</span> резонансных жалоб</h3>
                        <span style="margin-left: auto; background: #dfe6e9; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.85rem; color: #636e72;">🔽 от самых опасных</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.text_area("", text_output, height=500, label_visibility="collapsed")
                    st.download_button("📥 Скачать как .txt", data=text_output, file_name="резонанс_двор_баллы.txt", mime="text/plain")
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
                import traceback
                st.text(traceback.format_exc())

st.markdown('<div class="footer">🏡 Резонансный фильтр • Автоматический отбор опасных жалоб по дворовой территории</div>', unsafe_allow_html=True)

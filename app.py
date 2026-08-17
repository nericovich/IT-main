import streamlit as st
import pandas as pd
import json
import os
import random
from html import escape
from pathlib import Path

# Настройка страницы
st.set_page_config(page_title="Панель ведущего Бункер IT", page_icon="🤖", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
FILE_NAME = "Карты_Бункер_IT_Макс_Версия_30_карт.xlsx"
FILE_PATH = BASE_DIR / FILE_NAME
STATE_PATH = BASE_DIR / ".bunker_session.json"
GM_PASSWORD = os.getenv("BUNKER_GM_PASSWORD", "YA2077")

CATEGORY_ALIASES = {
    "Апакалипсис": "Апокалипсис",
}

@st.cache_data
def load_data():
    """Загружает данные из листов Excel, чтобы не читать файл при каждом клике"""
    if not FILE_PATH.exists():
        st.error(f"Файл {FILE_NAME} не найден рядом с app.py!")
        return None

    try:
        xl = pd.ExcelFile(FILE_PATH)
    except Exception as exc:
        st.error(f"Не удалось открыть Excel-файл: {exc}")
        return None

    sheets_data = {}

    # Загружаем индивидуальные листы категорий
    for sheet in xl.sheet_names:
        # Пропускаем первый общий лист, если он дублирует данные
        if "настольной игры" in sheet.lower():
            continue

        df = pd.read_excel(FILE_PATH, sheet_name=sheet)
        if df.shape[1] < 3:
            continue

        df = df.iloc[:, :3].copy()
        df.columns = ["Категория", "Название", "Описание"]
        # Убираем возможные пустые строки
        df = df.dropna(subset=["Название"])
        df = df.fillna("")

        sheet_name = sheet.strip()
        category_name = CATEGORY_ALIASES.get(sheet_name, sheet_name)
        sheets_data[category_name] = df.to_dict("records")

    return sheets_data


def get_random_card(category):
    """Возвращает случайную карту категории или безопасную заглушку."""
    return random.choice(data.get(category, [{"Название": "Неизвестно", "Описание": ""}]))


def draw_cards(category, count):
    """Тянет карты категории без повторов, пока хватает карт в колоде."""
    card_pool = data.get(category, [])
    if not card_pool:
        return []
    if count <= len(card_pool):
        return random.sample(card_pool, count)
    return [random.choice(card_pool) for _ in range(count)]


def normalize_card(card):
    return {
        "title": str(card.get("Название", "")),
        "description": str(card.get("Описание", "")),
    }


def generate_session(player_count, perks_per_player):
    player_categories = ["Профессия", "Биология", "Здоровье", "Хобби", "Багаж", "Факт"]
    session = {
        "generation_id": random.randint(100000, 999999),
        "world": [
            {
                "id": "world_apocalypse",
                "label": "🚨 Апокалипсис",
                **normalize_card(get_random_card("Апокалипсис")),
                "revealed": True,
                "accent_color": "#e11d48",
                "label_color": "#fda4af",
            },
            {
                "id": "world_bunker",
                "label": "🏢 Бункер",
                **normalize_card(get_random_card("Бункер")),
                "revealed": True,
                "accent_color": "#3b82f6",
                "label_color": "#93c5fd",
            },
            {
                "id": "world_threat",
                "label": "⚠️ Угроза",
                **normalize_card(get_random_card("Угроза")),
                "revealed": True,
                "accent_color": "#f59e0b",
                "label_color": "#fde047",
            },
        ],
        "players": [],
    }

    drawn_by_category = {
        category: draw_cards(category, player_count)
        for category in player_categories
    }
    drawn_perks = draw_cards("Перк", player_count * perks_per_player)

    for player_index in range(player_count):
        cards = []
        for card_index, category in enumerate(player_categories, 1):
            if drawn_by_category[category]:
                card = normalize_card(drawn_by_category[category][player_index])
                cards.append({
                    "id": f"p{player_index + 1}_card{card_index}",
                    "label": category,
                    **card,
                    "revealed": False,
                })

        perks_start = player_index * perks_per_player
        perks_end = perks_start + perks_per_player
        for perk_number, perk in enumerate(drawn_perks[perks_start:perks_end], 1):
            card = normalize_card(perk)
            cards.append({
                "id": f"p{player_index + 1}_perk{perk_number}",
                "label": f"Перк {perk_number}",
                **card,
                "perk_used": False,
                "revealed": False,
            })

        session["players"].append({
            "name": f"Игрок {player_index + 1}",
            "cards": cards,
        })

    return session


def load_saved_session():
    if not STATE_PATH.exists():
        return None

    try:
        session = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return ensure_session_perk_state(session)
    except (OSError, json.JSONDecodeError) as exc:
        st.warning(f"Не удалось загрузить сохранённую партию: {exc}")
        return None


def save_session(session):
    STATE_PATH.write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_saved_session():
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def render_world_card(label, title, description, accent_color, label_color):
    st.markdown(f"""
    <div class="bunker-section" style="border-left-color: {accent_color};">
        <span style="color: {label_color}; font-weight: bold; text-transform: uppercase; font-size: 12px;">{label}</span>
        <h3 style="margin: 5px 0; color: white;">{escape(str(title))}</h3>
        <p style="font-size: 14px; color: #cbd5e1; margin: 0;">{escape(str(description))}</p>
    </div>
    """, unsafe_allow_html=True)


def render_hidden_card(label):
    st.markdown(f"""
    <div class="hidden-card">
        <span class="hidden-tag">{escape(str(label))}</span>
        <div class="hidden-title">Закрыто ведущим</div>
    </div>
    """, unsafe_allow_html=True)


def render_player_card(label, title, description, color, extra_style="", status_html=""):
    with st.container(border=True):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f'<span style="display: inline-block; background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{escape(str(label))}</span>', unsafe_allow_html=True)
            st.markdown(f'**{escape(str(title))}**')
            st.markdown(escape(str(description)))
            if status_html:
                st.markdown(status_html, unsafe_allow_html=True)


def render_card(card):
    label = card["label"]
    base_category = label.split(" ")[0] if label.startswith("Перк") else label
    color = COLORS.get(base_category, "#334155")
    extra_style = "border-right: 4px dashed #db2777;" if base_category == "Перк" else ""
    status_html = ""
    if is_perk_card(card):
        if card.get("perk_used"):
            status_html = '<div style="margin-top: 8px; font-size: 13px; color: #15803d; font-weight: 600;">✅ Перк применён</div>'
    render_player_card(label, card["title"], card["description"], color, extra_style, status_html)


def render_player_cards(player, only_revealed=False):
    revealed_cards = 0
    for card in player["cards"]:
        if only_revealed and not card["revealed"]:
            render_hidden_card(card["label"])
            continue
        revealed_cards += 1
        render_card(card)
    return revealed_cards


def render_reveal_checkbox(session, card, key_prefix):
    revealed = st.checkbox(
        "Открыто",
        value=card["revealed"],
        key=f"{key_prefix}_{session['generation_id']}_{card['id']}",
    )
    if revealed != card["revealed"]:
        card["revealed"] = revealed
        save_session(session)
        st.rerun()


def is_perk_card(card):
    return str(card.get("label", "")).startswith("Перк")


FORBIDDEN_PERK_ACTIONS = [
    "перераздач",
    "переразд",
    "роли",
    "роль",
    "раздать роли",
    "перераспредел",
    "redistrib",
    "role",
]


def is_perk_applicable(card):
    if not is_perk_card(card):
        return False
    text = f"{card.get('title', '')} {card.get('description', '')}".lower()
    return not any(keyword in text for keyword in FORBIDDEN_PERK_ACTIONS)


def ensure_session_perk_state(session):
    for player in session.get("players", []):
        for card in player.get("cards", []):
            if is_perk_card(card) and "perk_used" not in card:
                card["perk_used"] = False
    return session


def render_world(session, player_view=False):
    world_cols = st.columns(3)
    for column, world_card in zip(world_cols, session["world"]):
        with column:
            if player_view and not world_card["revealed"]:
                render_hidden_card(world_card["label"])
            else:
                render_world_card(
                    world_card["label"],
                    world_card["title"],
                    world_card["description"],
                    world_card["accent_color"],
                    world_card["label_color"],
                )


def render_gm_player_controls(session, player, index):
    with st.expander(f"{player['name']} · {len(player['cards'])} карт", expanded=False):
        name = st.text_input(
            "Имя игрока",
            value=player["name"],
            key=f"player_name_{session['generation_id']}_{index}",
        )
        if name.strip() and name.strip() != player["name"]:
            player["name"] = name.strip()
            save_session(session)

        open_col, close_col = st.columns(2)
        with open_col:
            if st.button("Открыть все", key=f"open_all_{session['generation_id']}_{index}"):
                for card in player["cards"]:
                    card["revealed"] = True
                    st.session_state[f"reveal_player_{session['generation_id']}_{card['id']}"] = True
                save_session(session)
                st.rerun()
        with close_col:
            if st.button("Закрыть все", key=f"close_all_{session['generation_id']}_{index}"):
                for card in player["cards"]:
                    card["revealed"] = False
                    st.session_state[f"reveal_player_{session['generation_id']}_{card['id']}"] = False
                save_session(session)
                st.rerun()

        for card in player["cards"]:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                render_reveal_checkbox(session, card, "reveal_player")
            with col2:
                pass
            render_card(card)
            if is_perk_card(card):
                if card.get("perk_used"):
                    st.success("Перк уже применён")
                    if st.button(
                        "Отозвать применение",
                        key=f"reset_perk_{session['generation_id']}_{card['id']}",
                    ):
                        card["perk_used"] = False
                        save_session(session)
                        st.rerun()
                elif not card["revealed"]:
                    st.info("Перк будет доступен для применения после открытия.")
                else:
                    if is_perk_applicable(card):
                        if st.button(
                            "Применить перк",
                            key=f"apply_perk_{session['generation_id']}_{card['id']}",
                        ):
                            card["perk_used"] = True
                            save_session(session)
                            st.rerun()
                    else:
                        st.warning(
                            "Этот перк нельзя применять автоматически. Используйте его как правило игры."
                        )


def get_revealed_count(player):
    return sum(1 for card in player["cards"] if card["revealed"])


def render_gm_world_controls(session):
    st.caption("Мировые карты можно тоже скрывать или открывать для игроков.")
    for world_card in session["world"]:
        render_reveal_checkbox(session, world_card, "reveal_world")


def is_gm_authenticated():
    return st.session_state.get("gm_authenticated", False)


def render_gm_login():
    st.title("🔐 Вход ведущего")
    st.markdown(
        "<div class='gm-note'>Режим ведущего закрыт паролем. Игрокам доступно только общее табло.</div>",
        unsafe_allow_html=True,
    )

    password = st.text_input("Пароль ведущего", type="password")
    if st.button("Войти", type="primary"):
        if password == GM_PASSWORD:
            st.session_state.gm_authenticated = True
            st.rerun()
        else:
            st.error("Неверный пароль.")


data = load_data()

# Кастомные стили для карточек
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        font-size: 18px;
        font-weight: bold;
        padding: 12px;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        color: white;
    }
    .bunker-section {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #e11d48;
    }
    .player-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .card-tag {
        display: inline-block;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: 4px;
        color: white;
        margin-bottom: 5px;
    }
    .title-text {
        font-size: 16px;
        font-weight: bold;
        color: #1e293b;
    }
    .hidden-card {
        background-color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px dashed #94a3b8;
    }
    .hidden-tag {
        display: inline-block;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: 4px;
        color: #475569;
        background: #e2e8f0;
        margin-bottom: 5px;
    }
    .hidden-title {
        font-size: 15px;
        font-weight: bold;
        color: #64748b;
    }
    .perk-used {
        margin-top: 8px;
        font-size: 13px;
        color: #15803d;
        font-weight: 600;
    }
    .gm-note {
        color: #475569;
        font-size: 14px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Цвета тегов для визуала
COLORS = {
    "Профессия": "#2563eb", "Биология": "#059669", "Здоровье": "#d97706",
    "Хобби": "#7c3aed", "Багаж": "#475569", "Факт": "#0891b2", "Перк": "#db2777"
}

if data:
    saved_session = load_saved_session()

    with st.sidebar:
        role = st.radio("Режим", ["Игрок", "Ведущий"], horizontal=True)
        st.markdown("---")

    if role == "Ведущий":
        if not is_gm_authenticated():
            render_gm_login()
            st.stop()

        st.title("🤖 Панель ведущего «Бункер IT»")
        st.markdown(
            "<div class='gm-note'>Система выдаёт карты для раздачи игрокам. Ведущий раздаёт их и открывает характеристики на общем табло по ходу игры.</div>",
            unsafe_allow_html=True,
        )

        with st.sidebar:
            st.header("Настройки партии")
            player_count = st.number_input("Количество игроков", min_value=2, max_value=30, value=6, step=1)
            perks_per_player = st.number_input("Перков на игрока", min_value=0, max_value=5, value=2, step=1)

            if st.button("🔄 Сгенерировать новую партию", type="primary"):
                session = generate_session(player_count, perks_per_player)
                save_session(session)
                st.rerun()

            if saved_session and st.button("🧹 Очистить стол"):
                clear_saved_session()
                st.rerun()

            if st.button("Выйти из режима ведущего"):
                st.session_state.gm_authenticated = False
                st.rerun()

        if not saved_session:
            st.info("Выбери количество игроков в панели слева и нажми «Сгенерировать новую партию».")
        else:
            session = saved_session

            st.subheader("🌍 Мир партии")
            render_world(session)
            render_gm_world_controls(session)

            st.markdown("---")
            st.subheader("🪪 Карты игроков")

            for index, player in enumerate(session["players"], 1):
                revealed_count = get_revealed_count(player)
                player["name"] = player.get("name") or f"Игрок {index}"
                with st.container():
                    st.caption(f"{player['name']}: открыто {revealed_count} из {len(player['cards'])}")
                render_gm_player_controls(session, player, index)

    else:
        st.title("🪪 Табло игроков «Бункер IT»")
        st.markdown(
            "<div class='gm-note'>Здесь видны все игроки. Содержимое характеристик появляется только после того, как ведущий его откроет.</div>",
            unsafe_allow_html=True,
        )

        if not saved_session:
            st.info("Партия ещё не создана. Подожди, пока ведущий сгенерирует стол.")
        else:
            session = saved_session
            players = session["players"]

            with st.sidebar:
                if st.button("↻ Обновить"):
                    st.rerun()

            st.subheader("🌍 Мир партии")
            render_world(session, player_view=True)

            st.markdown("---")
            st.subheader("👥 Игроки")

            player_columns = st.columns(2)
            for index, player in enumerate(players, 1):
                player["name"] = player.get("name") or f"Игрок {index}"
                revealed_count = get_revealed_count(player)
                with player_columns[(index - 1) % 2]:
                    with st.expander(
                        f"{player['name']} · открыто {revealed_count} из {len(player['cards'])}",
                        expanded=True,
                    ):
                        render_player_cards(player, only_revealed=True)

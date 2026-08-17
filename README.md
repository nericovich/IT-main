# Бункер IT

Streamlit-приложение для ведущего и игроков.

## Режимы

- `Игрок`: публичное табло всех игроков. Закрытые характеристики видны как слоты, содержимое появляется после открытия ведущим.
- `Ведущий`: генерация партии, раздача карт игрокам и управление раскрытием характеристик. Пароль по умолчанию: `YA2077`.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Запуск на сервере

```bash
export BUNKER_GM_PASSWORD="YA2077"
streamlit run app.py --server.port 8501
```

Для VPS обычно открывают приложение через reverse proxy на порт Streamlit. Файл партии сохраняется в `.bunker_session.json` рядом с приложением и не входит в git.

## Docker

```bash
docker build -t bunker-it .
docker run -d --name bunker-it -p 8501:8501 -e BUNKER_GM_PASSWORD="YA2077" bunker-it
```

## Файлы релиза

- `app.py` — приложение.
- `requirements.txt` — Python-зависимости.
- `.streamlit/config.toml` — серверный конфиг Streamlit.
- `Dockerfile` — контейнерный запуск.
- `Карты_Бункер_IT_Макс_Версия_30_карт.xlsx` — данные карт.

# 📡 Bybit Streaming Collector

Модуль для подключения к **Bybit WebSocket API** через библиотеку [`pybit`](https://github.com/bybit-exchange/pybit-unified),
с возможностью масштабирования, авто-переподключения и отправки данных в **Redis Pub/Sub**.

---

## 🧱 Структура проекта

```
project_root/
├── main.py                 # Главный модуль: управление всеми сокетами и потоками
├── callbacks/
│   ├── orderbook.py        # Callback для ордербука
│   ├── trades.py           # Callback для сделок
│   ├── ticker.py           # Callback для тикера
│   └── liquidations.py     # Callback для ликвидаций
├── conf/
│   └── settings.py         # Настройки, включая подключение к Redis и параметры WebSocket
└── .env                    # Секреты и переменные окружения (REDIS_HOST, REDIS_PORT, ...)
```

---

## ⚙️ Настройки (`conf/settings.py`)

Параметры WebSocket и Redis управляются через `.env`:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

```python
USE_TESTNET = True         # True = testnet.bybit.com, False = mainnet.bybit.com
CHANNEL_TYPE = "linear"    # тип каналов (spot / linear / inverse)
RECONNECT_DELAY = 2        # пауза перед переподключением, в секундах
```

---

## 🔌 Поддерживаемые WebSocket-каналы

| Канал             | Метод подписки                            | Callback-функция        | Пример Redis-канала               |
|-------------------|-------------------------------------------|--------------------------|----------------------------------|
| **OrderBook**     | `orderbook_stream(depth=50, symbol=...)`  | `handle_orderbook`       | `stream:bybit_orderbook`         |
| **Trades**        | `trade_stream(symbol=...)`                 | `handle_trades`          | `stream:bybit_trades`            |
| **Ticker**        | `ticker_stream(symbol=...)`                | `handle_ticker`          | `stream:bybit_ticker`            |
| **Liquidations**  | `all_liquidation_stream(symbol=...)`       | `handle_liquidations`    | `stream:bybit_liquidations`      |

---

## 🧠 Типы данных, которые приходят из Bybit

### 📘 OrderBook (`orderbook.50.<SYMBOL>`)
```json
{
  "topic": "orderbook.50.BTCUSDT",
  "type": "snapshot",
  "ts": 1761884492344,
  "data": {
    "s": "BTCUSDT",
    "b": [["1947617.90", "0.770"], ["1947226.70", "2.000"]],
    "a": [["1999999.80", "498.000"]],
    "u": 190368,
    "seq": 9538517779
  },
  "cts": 1761884492322
}
```
**b** — bids (покупатели), **a** — asks (продавцы).

---

### 📗 Trades (`publicTrade.<SYMBOL>`)
```json
{
  "topic": "publicTrade.BTCUSDT",
  "type": "snapshot",
  "ts": 1761884491021,
  "data": [
    {
      "T": 1761884491018,
      "s": "BTCUSDT",
      "S": "Sell",
      "v": "0.015",
      "p": "1947617.90",
      "L": "ZeroMinusTick",
      "i": "665b94d1-50af-54f3-bcb9-13ea63750ecf"
    }
  ]
}
```
**S** — направление (Buy/Sell), **v** — объём, **p** — цена.

---

### 📙 Ticker (`tickers.<SYMBOL>`)
```json
{
  "topic": "tickers.BTCUSDT",
  "type": "snapshot",
  "data": {
    "symbol": "BTCUSDT",
    "lastPrice": "1947617.90",
    "highPrice24h": "1999999.80",
    "lowPrice24h": "1616450.10",
    "volume24h": "27815.4710",
    "turnover24h": "53452994895.9110",
    "fundingRate": "0.005",
    "bid1Price": "1947617.90",
    "ask1Price": "1999989.80"
  },
  "ts": 1761884491972
}
```

---

### 📕 Liquidations (`allLiquidation.<SYMBOL>`)
```json
{
  "topic": "allLiquidation.ROSEUSDT",
  "type": "snapshot",
  "ts": 1739502303204,
  "data": [
    {
      "T": 1739502302929,
      "s": "ROSEUSDT",
      "S": "Sell",
      "v": "20000",
      "p": "0.04499"
    }
  ]
}
```
**S** — направление ликвидации, **v** — объём ликвидируемой позиции, **p** — цена ликвидации.

---

## 🧾 Формат сообщений в Redis Pub/Sub

Каждый callback публикует данные в свой канал Redis.  
Сообщение — это **JSON** в оригинальном виде от Bybit WebSocket API.

| Redis канал                | Описание данных                   | Пример |
|-----------------------------|------------------------------------|---------|
| `stream:bybit_orderbook`    | Структура ордербука (bid/ask)     | `{"topic": "orderbook.50.BTCUSDT", "data": {...}}` |
| `stream:bybit_trades`       | Список последних сделок           | `{"topic": "publicTrade.BTCUSDT", "data": [...]}` |
| `stream:bybit_ticker`       | Текущие данные тикера             | `{"topic": "tickers.BTCUSDT", "data": {...}}` |
| `stream:bybit_liquidations` | События ликвидаций                | `{"topic": "allLiquidation.ROSEUSDT", "data": [...]}` |

**Важно:** сообщения передаются «как есть» без изменения, чтобы downstream-сервисы могли парсить их самостоятельно.

---

## 🚀 Как работает `main.py`

- Каждый стрим создаётся как отдельный **поток** (`threading.Thread`).
- При падении соединения поток **автоматически переподключается** через `RECONNECT_DELAY` секунд.
- Все данные передаются в Redis Pub/Sub по именованным каналам.

---

## ▶️ Запуск

```bash
python main.py
```

Для production можно использовать `supervisor`, `systemd` или Docker.

---

## 🧰 Зависимости

```bash
pip install pybit redis python-dotenv
```

---

## 📡 Масштабирование

Чтобы добавить новый стрим — просто расширь список `STREAMS` в `main.py`:

```python
STREAMS.append({
    "name": "Trades_ETHUSDT",
    "func": subscribe_trades,
    "args": ("ETHUSDT", handle_trades)
})
```

После этого новый поток автоматически подключится и начнёт публиковать данные в Redis.

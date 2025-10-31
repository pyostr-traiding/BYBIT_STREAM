import time
import threading

from pybit.unified_trading import WebSocket

from conf.settings import USE_TESTNET, CHANNEL_TYPE, RECONNECT_DELAY

from callbacks.liquidations import handle_liquidations
from callbacks.orderbook import handle_orderbook
from callbacks.ticker import handle_ticker
from callbacks.trades import handle_trades


# ===== КЛАСС ПОДКЛЮЧЕНИЯ =====
class WSConnection(threading.Thread):
    """
    Один экземпляр этого класса управляет подключением к определённому стриму.
    При обрыве — переподключается автоматически.
    """
    def __init__(self, name, subscribe_func, *args, **kwargs):
        super().__init__()
        self.name = name
        self.subscribe_func = subscribe_func
        self.args = args
        self.kwargs = kwargs
        self.daemon = True
        self.running = True

    def run(self):
        while self.running:
            try:
                print(f"[{self.name}] Подключаюсь к сокету...")
                ws = WebSocket(
                    testnet=USE_TESTNET,
                    channel_type=CHANNEL_TYPE
                )

                # подписка
                self.subscribe_func(ws, *self.args, **self.kwargs)
                print(f"[{self.name}] Подключен успешно!")

                # держим поток живым
                while self.running:
                    time.sleep(1)

            except Exception as e:
                print(f"[{self.name}] Ошибка: {e}, переподключаюсь через {RECONNECT_DELAY} сек...")
                time.sleep(RECONNECT_DELAY)

    def stop(self):
        self.running = False


# ===== ПОДПИСКИ =====
def subscribe_orderbook(ws, symbol, callback):
    ws.orderbook_stream(depth=50, symbol=symbol, callback=callback)

def subscribe_trades(ws, symbol, callback):
    ws.trade_stream(symbol=symbol, callback=callback)

def subscribe_ticker(ws, symbol, callback):
    ws.ticker_stream(symbol=symbol, callback=callback)

def subscribe_liquidations(ws, symbol, callback):
    ws.all_liquidation_stream(symbol=symbol, callback=callback)


# ===== КОНФИГ СТРИМОВ =====
STREAMS = [
    {
        "name": "OrderBook_BTCUSDT",
        "func": subscribe_orderbook,
        "args": ("BTCUSDT", handle_orderbook)
    },
    {
        "name": "Trades_BTCUSDT",
        "func": subscribe_trades,
        "args": ("BTCUSDT", handle_trades)
    },
    {
        "name": "Ticker_BTCUSDT",
        "func": subscribe_ticker,
        "args": ("BTCUSDT", handle_ticker)
    },
    {
        "name": "Liquidations_BTCUSDT",
        "func": subscribe_liquidations,
        "args": ("BTCUSDT", handle_liquidations)
    },
    # сюда можно добавлять сколько угодно стримов
]


# ===== ЗАПУСК =====
if __name__ == "__main__":
    connections = []

    for stream in STREAMS:
        conn = WSConnection(
            stream["name"],  # name
            stream["func"],  # subscribe_func
            *stream["args"]  # позиционные аргументы
        )
        conn.start()
        connections.append(conn)

    print("[MAIN] Все сокеты запущены.")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[MAIN] Остановка всех соединений...")
        for conn in connections:
            conn.stop()
        print("[MAIN] Завершено.")

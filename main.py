import asyncio
import aiohttp
import time
import os
from aiohttp_socks import ProxyConnector

# --- НАСТРОЙКИ ---
INPUT_FILE = "proxy.txt"
OUTPUT_FILE = "valid_proxies.txt"
TARGET_URL = "https://google.com"
TIMEOUT = 10
PROTOCOL = "http://"
TIMEOUT = 10
# Укажите протокол ваших прокси (http или socks5)
PROTOCOL = "http"


def load_proxies():
    """Загружает прокси из файла и готовит данные для проверки"""
    if not os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "w", encoding="utf-8") as f:
            pass
        print(f"⚠️ Файл {INPUT_FILE} не найден. Создан пустой файл. Заполните его.")
        return [ ]

    proxy_data = [ ]
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.count(':') != 3:
                if line: print(f"⚠️ Пропущена строка (неверный формат): {line}")
                continue

            # Разбираем строку IP:PORT:LOGIN:PASS
            parts = line.split(":")
            ip, port, login, password = parts

            # Формируем URL для библиотеки
            url = f"{PROTOCOL}://{login}:{password}@{ip}:{port}"

            # Сохраняем и URL для проверки, и исходную строку для вывода
            proxy_data.append({
                'url': url,
                'raw': line
            })

    return proxy_data


async def check_proxy(proxy_item):
    """Проверяет прокси и возвращает (raw_string, ping) или None"""
    proxy_url = proxy_item[ 'url' ]
    raw_str = proxy_item[ 'raw' ]

    try:
        connector = ProxyConnector.from_url(proxy_url)
        timeout_cfg = aiohttp.ClientTimeout(total=TIMEOUT)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout_cfg) as session:
            start = time.perf_counter()
            async with session.get(TARGET_URL) as response:
                if response.status == 200:
                    latency = round((time.perf_counter() - start) * 1000)
                    print(f"[✅ OK] {raw_str:<30} | Ping: {latency:>4}ms")
                    return (raw_str, latency)
    except:
        pass
    return None


async def main():
    proxies = load_proxies()

    if not proxies:
        print("Список прокси пуст. Добавьте прокси в proxy.txt (IP:PORT:LOGIN:PASS)")
        return

    print(f"🚀 Проверка {len(proxies)} прокси через {TARGET_URL}...")
    print("-" * 65)

    tasks = [ check_proxy(p) for p in proxies ]
    results = await asyncio.gather(*tasks)

    # Фильтруем рабочие и сортируем по пингу
    valid_results = sorted([ res for res in results if res ], key=lambda x: x[ 1 ])

    print("-" * 65)
    print(f"📊 Итог: {len(valid_results)} рабочих прокси.")

    if valid_results:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for raw, _ in valid_results:
                f.write(f"{raw}\n")
        print(f"💾 Список сохранен в '{OUTPUT_FILE}' в исходном формате.")
    else:
        print("❌ Рабочих прокси не найдено.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПроверка прервана пользователем.")
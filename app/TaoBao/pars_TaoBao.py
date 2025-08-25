import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def fetch_and_parse(search_query):
    # Используем f-строку для правильной подстановки поискового запроса в URL
    url = f'https://s.taobao.com/search?q={search_query}&_input_charset=utf-8&commend=all&search_type=item'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            response.raise_for_status() # Рекомендуется проверять статус ответа
            print(response.status)

            # Получаем текст ответа один раз
            html_text = await response.text()

            with open('page_text.txt', 'w', encoding='utf-8') as f:
                f.write(html_text)

            # Создаем объект BeautifulSoup для парсинга
            # 'lxml' - быстрый парсер, который вы установили.
            # Можно использовать встроенный 'html.parser', но он медленнее.
            soup = BeautifulSoup(html_text, 'lxml')

            # --- Пример парсинга ---
            # Например, найдем заголовок страницы (тег <title>)
            title_tag = soup.find('title')
            if title_tag:
                print(f"Заголовок страницы: {title_tag.get_text(strip=True)}")


if __name__ == '__main__':
    # Ввод запроса и запуск асинхронной функции должны быть здесь
    search_query = input('Введите поисковый запрос: ')
    # Это современный и правильный способ запуска асинхронной функции
    asyncio.run(fetch_and_parse(search_query))
# Библиотеки, которые могут вам понадобиться
# При необходимости расширяйте список
import time
import requests
import schedule
import re
from bs4 import BeautifulSoup


def get_book_data(url: str, timeout: int = 15, debug: bool = False) -> dict:
    """
    Функция загружает страницу одной книги по заданному url и возращает результаты парсинга страницы с книгой.

    Args:
        url (str): полный url детальной страницы книги.
        timeout (int): таймаут запроса в секундах (по умолчанию 15).

    Returns:
        dict: Словарь с ключами:
            - title (str | None): Название книги
            - price (float | None): Значение цены
            - rating (int): Рейтинг по звездам (1..5; 0 - если не найден).
            - availability (int): Количество в наличии (целое число; 0 - есои не найден).
            - description (str | None): Краткое описание.
            - product_information (dict): Пары из таблицы Product Information.
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ

    response = requests.get(url, timeout=timeout)  
    response.raise_for_status()  # исключение, если код ответа != 200

    # без utf8 символ £ спарсится как Â£
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")  # , from_encoding="utf-8"
    
    main = soup.select_one("div.product_main")  # главный div

    #  1. название
    title_tag = main.find("h1") if main else None  
    title = title_tag.get_text(strip=True) if title_tag else None
    if debug:
        print("название: ", title)

    
    #  2. цена
    price_tag = main.select_one(".price_color") if main else None  
    price_raw = price_tag.get_text(strip=True) if price_tag else None  
    price = None
    
    if price_raw:
        m = re.search(r"(\d+(?:\.\d+)?)", price_raw)  # забираем число с точкой, без сивмола валюты
        price = float(m.group(1)) if m else None

        if debug:
            print("цена строкой: ", price_raw)
            print("цена числом: ", price)

    
    #  3. рейтинг
    rating_words_to_int = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}  # "No rating": 0,
    rating = 0  # дефолтный
    
    rating_tag = main.select_one(".star-rating") if main else None  

    if rating_tag:  
        for cls in rating_tag.get("class", []):  
            if cls in rating_words_to_int:  
                rating = rating_words_to_int[cls]
                if debug:
                    print("рейтинг: ", rating)
                break

    #  4. наличие: 
    #  <p class="instock availability"><i class="icon-ok"></i>In stock (22 available)</p>
    
    availability = 0  
    availability_tag = soup.select_one("p.instock.availability")  
    
    if availability_tag:  
        availability_text = availability_tag.get_text(strip=True)  
        
        match = re.search(r"(\d+)", availability_text)  # ищем число
        
        if match:  
            availability = int(match.group(1))
            if debug:
                print("строка с инф о наличии: ", availability_text)
                print("наличие в штуках: ", availability)


    #  5. Описание книги 
    #  <div id="product_description" class="sub-header"><h2></h2></div><p>
    
    description = None
    desc_header = soup.find(id="product_description")
    if desc_header:
        desc_paragraph = desc_header.find_next("p")
        if desc_paragraph:
            description = desc_paragraph.get_text(strip=True)
            if debug:
                print(f"\nОписание книги: {description} \n")
    
    
    #  6. Таблица product information "table table-striped"
    product_info_table = soup.select_one("table.table.table-striped")
    product_information = {} 
    if product_info_table:  
        rows = product_info_table.select("tr")  

        if debug:
            print("\nпробуем получить параметры книги:\n")
            
        for row in rows:  
            th = row.find("th")  
            td = row.find("td")  
            if th and td:  
                key = th.get_text(strip=True)  
                value = td.get_text(strip=True)  
                product_information[key] = value  
                if debug:
                    print(f"Параметр {key} = {value}")
                
    #  7. итого

    #  price_raw и availability_text не возвращается в результатах, но они есть в режиме отладки
    result = {
        "title": title,  
        "price": price,  
        "rating": rating,  
        "availability": availability,  
        "description": description,  
        "product_information": product_information,  
    }

    return result

print("\nИспользуем debug=True для демонстрации / отладки работы функции: \n")
book_url = 'http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
res = get_book_data(book_url, debug=True)
# print(res)

    # КОНЕЦ ВАШЕГО РЕШЕНИЯ
    

def scrape_books(base_pattern: str,
                 save_to_file: bool = False,
                 timeout: int = 15,
                 debug: bool = False) -> list:
    """
    
    Функция обходит каталог книг по шаблону url формата '.../page-{N}.html' и
    собирает данные всех книг со всех страниц, использую кнопку Next для определения,
    есть ли еще доступные страницы листингов.

    Args:
        - base_pattern (str): шаблон url с подстановкой {N}. 
        Пример: 'http://books.toscrape.com/catalogue/page-{N}.html'.
        
        - save_to_file (bool): если True — сохраняет результат в books_data.txt (по 1-й строке на книгу).
        
        - timeout (int): Таймаут HTTP-запроса в секундах
        - debug (bool): для режима отладки

    Returns:
        list[dict]: Список словарей, каждый из них - результат вызова get_book_data() для одной книги.
        
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    all_books = []
    
    n = 0

    while True:
        
        n += 1
        
        page_url = base_pattern.replace("{N}", str(n))
        
        if debug:
            print(f"\nПарсим страницу №{n}: {page_url}")
            
        resp = requests.get(page_url, timeout=timeout)

        if resp.status_code == 404:
            if debug:
                print("err 404, что-то пошло не так :)")
            break

        if resp.status_code != 200:  # обрабатываем только 200 ответы, без 304, 301 
            resp.raise_for_status()

        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select("article.product_pod")  
        
        if debug:
            print("карточек на странице: ", len(cards))

        #  кнопки "Next" для перехода на след страницу имеют ссылки вида: page-4.html, соотв. нужнен base dir
        #  чтобы сформировать финальный url
        
        cut = page_url.rfind("/")                                  
        base_dir = page_url[:cut + 1] if cut != -1 else page_url + "/"

        SITE_ROOT = "https://books.toscrape.com/"

        for card in cards:
            a_tag = card.select_one("h3 a")
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            
            #  делаем поддержку всех типов ссылок: абсолютные, короткие "//somelink", относительные, и ссылки требующих base_dir
            if href.startswith("http://") or href.startswith("https://"):
                book_url = href
            elif href.startswith("/"):
                book_url = SITE_ROOT + href.lstrip("/")
            else:
                cut = page_url.rfind("/")
                base_dir = page_url[:cut + 1] if cut != -1 else page_url + "/"
                book_url = base_dir + href

            if debug:
                #  print("raw ссылка: ", href)
                print("ссылка на книгу: ", book_url)

            try:
                data = get_book_data(book_url, timeout=timeout, debug=False)
                all_books.append(data)
            except Exception as err:
                if debug:
                    print("ошибка парсинга: ", err)
                    
        #  ищем ссылку на след. страницу (кнопка Next), если она есть - продолжаем while, иначе останавливаем цикл
        has_next = soup.select_one("li.next > a") is not None 
        if not has_next:
            if debug:
                print("нет ссылки на слет страницу ")
            break  # выходим из while(true)
        
        
        #if n > 1:  # ограничиваем 1 страницу для автотестов
            #break

    if save_to_file:
        if debug:
            print("\сохранение в файл")
        with open("books_data.txt", "w", encoding="utf-8") as f:
            for item in all_books:
                f.write(str(item) + "\n")

    return all_books

    
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ

# денострация работы в режиме отладки 
# в итоге отключил режим отладки, т.к. огромное полотно получается print'ов
# pattern = "http://books.toscrape.com/catalogue/page-{N}.html"
# result = scrape_books(pattern, save_to_file=True, debug=False)




from scraper import get_book_data, scrape_books

def test_get_book_data_keys_and_title():
    """
    Проверяет, что функция get_book_data возвращает словарь
    с нужными ключами и корректным названием книги
    """
    url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    d = get_book_data(url)
    for k in ("title", "price", "rating", "availability", "description", "product_information"):
        assert k in d
    assert d["title"] == "A Light in the Attic"


def test_get_book_data_price_and_rating():
    """
    Проверяет, что цена положительная, а рейтинг находится в диапазоне 0 - 5
    """
    url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    d = get_book_data(url)
    assert d["price"] is None or d["price"] > 0
    assert 0 <= d["rating"] <= 5


def test_scrape_books_first_page_min():
    """
    Проверяет, что с первой страницы каталога парсится не меньше 20 книг.
    """
    pattern = "http://books.toscrape.com/catalogue/page-{N}.html"
    data = scrape_books(pattern, save_to_file=False, debug=False)
    assert isinstance(data, list)
    assert len(data) >= 20
    assert isinstance(data[0], dict)
    assert "title" in data[0]
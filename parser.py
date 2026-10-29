import requests
import pandas as pd
import json
import io
import re
import datetime

def run():
    print("Начинаю работу...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        page = requests.get("https://rosstat.gov.ru/statistics/price", headers=headers).text
        links = re.findall(r'href="([^"]+\.xlsx)"', page)
        
        file_url = None
        for link in links:
            if 'potreb' in link.lower() or 'cen' in link.lower():
                file_url = link if link.startswith('http') else f"https://rosstat.gov.ru{link}"
                break
                
        if not file_url:
            file_url = "https://rosstat.gov.ru/storage/mediabank/ind_potreb_cen.xlsx"

        print(f"Скачиваю: {file_url}")
        response = requests.get(file_url, headers=headers)
        df = pd.read_excel(io.BytesIO(response.content), header=None)
        
        # Улучшенный список товаров: теперь ищем по корню слова
        targets = [
            "Помидор", "Огурц", "Банан", "Картофел", "Морков", "Капуст", 
            "Свекл", "Яблок", "Бензин", "Говядин", "Свинин", "Кур", 
            "Окорочк", "Индейк", "Фарш", "Сосиск", "Сардельк", "Пельмен", "Сельд", 
            "Яйц", "Молок", "Сметан", "Сыр", "Масло сливочн", 
            "Хлеб", "Рис", "Вермишел", "Мука", "Сахар", "Масло подсолнечн", 
            "Маргарин", "Чай", "Печень", "Мыло", "Зубная паст"
        ]
        
        goods = []
        for index, row in df.iterrows():
            row_str = str(row.values)
            for t in targets:
                if t in row_str:
                    # Ищем проценты. Обычно в Росстате изменение цен имеет знак + или -
                    # Пытаемся найти подходящее число (от -100 до 100)
                    for val in reversed(row.values):
                        try:
                            clean_val = str(val).replace(',', '.').replace('%', '').strip()
                            num = float(clean_val)
                            # Если число похоже на процент изменения (не гигантская цена)
                            if -100 < num < 100:
                                if not any(g['name'] == t for g in goods):
                                    goods.append({"name": t, "value": num})
                                break
                        except ValueError:
                            continue

        print(f"Найдено товаров: {len(goods)}")
        
        if len(goods) > 0:
            with open('data.json', 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                
            current_data['goods'] = goods
            current_data['last_updated'] = str(datetime.datetime.now())
            
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            print("Данные сохранены!")
        else:
            print("Товары не распознаны. Оставляем старые данные.")
            
    except Exception as e:
        print(f"Ошибка: {e}. Оставляем старые данные.")

if __name__ == "__main__":
    run()

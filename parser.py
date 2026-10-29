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
        # 1. Ищем актуальную ссылку на файл на сайте Росстата
        page = requests.get("https://rosstat.gov.ru/statistics/price", headers=headers).text
        links = re.findall(r'href="([^"]+\.xlsx)"', page)
        
        file_url = None
        for link in links:
            if 'potreb' in link.lower() or 'cen' in link.lower():
                file_url = link if link.startswith('http') else f"https://rosstat.gov.ru{link}"
                break
                
        if not file_url:
            print("Ссылка не найдена, использую прямую.")
            file_url = "https://rosstat.gov.ru/storage/mediabank/ind_potreb_cen.xlsx"

        print(f"Скачиваю: {file_url}")
        response = requests.get(file_url, headers=headers)
        
        # 2. Читаем Excel
        df = pd.read_excel(io.BytesIO(response.content), header=None)
        
        # 3. Ищем товары
        targets = ["Помидоры", "Огурцы", "Бананы", "Картофель", "Морковь", "Капуста", 
                   "Свекла", "Яблоки", "Бензин", "Говядина", "Свинина", "Куры", 
                   "Окорочка", "Индейка", "Фарш", "Сосиски", "Пельмени", "Сельдь", 
                   "Яйца", "Молоко", "Сметана", "Сыры", "Масло сливочное", 
                   "Хлеб", "Рис", "Вермишель", "Мука", "Сахар", "Масло подсолнечное", 
                   "Маргарин", "Чай", "Печенье", "Мыло", "Зубная паста"]
        
        goods = []
        for index, row in df.iterrows():
            row_str = str(row.values)
            for t in targets:
                if t in row_str:
                    for val in reversed(row.values):
                        try:
                            clean_val = str(val).replace(',', '.').replace('%', '').strip()
                            num = float(clean_val)
                            if not any(g['name'] == t for g in goods):
                                goods.append({"name": t, "value": num})
                            break
                        except ValueError:
                            continue

        print(f"Найдено товаров: {len(goods)}")
        
        # 4. Сохраняем в JSON (если нашли данные)
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

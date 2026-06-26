from connect import (
    db, Category, CategoryQuote,
    Motivation, Affirmation, FunnyQuote,
    sync_categories_to_file, sync_quotes_to_categories_file
)
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_categories():
    """Создание категорий с чёткими границами"""
    categories_data = [
    {
        "name": "Успех и достижения",
        "description": "Цитаты о достижении целей, успехе, победах и реализации потенциала",
        "type": "motivation"
    },
    {
        "name": "Лидерство и влияние",
        "description": "Мудрость о лидерстве, управлении людьми и влиянии на мир",
        "type": "motivation"
    },
    {
        "name": "Саморазвитие и рост",
        "description": "Цитаты о личностном росте, обучении, изменениях и самосовершенствовании",
        "type": "motivation"
    },
    {
        "name": "Преодоление трудностей",
        "description": "Вдохновляющие слова о смелости, преодолении страхов и неудач",
        "type": "motivation"
    },
    {
        "name": "Дисциплина и настойчивость",
        "description": "Цитаты о важности дисциплины, упорства, привычек и постоянства",
        "type": "motivation"
    },
    {
        "name": "Мудрость жизни",
        "description": "Глубокие философские мысли о жизни, судьбе и человеческой природе",
        "type": "motivation"
    },
    {
        "name": "Действие и решимость",
        "description": "Призывы к действию, важность первого шага и решительности",
        "type": "motivation"
    },
    {
        "name": "Любовь к себе",
        "description": "Аффирмации для развития самооценки, принятия и любви к себе",
        "type": "affirmation"
    },
    {
        "name": "Финансовое благополучие",
        "description": "Утверждения для привлечения денег, изобилия и процветания",
        "type": "affirmation"
    },
    {
        "name": "Здоровье и энергия",
        "description": "Аффирмации для физического здоровья, vitality и исцеления",
        "type": "affirmation"
    },
    {
        "name": "Отношения и гармония",
        "description": "Утверждения для создания гармоничных отношений с людьми",
        "type": "affirmation"
    },
    {
        "name": "Внутренний покой",
        "description": "Аффирмации для успокоения ума, принятия и душевного равновесия",
        "type": "affirmation"
    },
    {
        "name": "Уверенность и сила",
        "description": "Утверждения для развития уверенности, силы духа и решимости",
        "type": "affirmation"
    },
    {
        "name": "Благодарность и радость",
        "description": "Аффирмации для культивирования благодарности и счастья",
        "type": "affirmation"
    },
    {
        "name": "Жизненная ирония",
        "description": "Смешные и ироничные наблюдения о жизни и её парадоксах",
        "type": "funny"
    },
    {
        "name": "Лень и прокрастинация",
        "description": "Юмор о желании ничего не делать и откладывании дел",
        "type": "funny"
    },
    {
        "name": "Возраст и старение",
        "description": "Смешные цитаты о возрасте, взрослении и старении",
        "type": "funny"
    },
    {
        "name": "Отношения и быт",
        "description": "Юмор о семейной жизни, отношениях и бытовых ситуациях",
        "type": "funny"
    },
    {
        "name": "Работа и карьера",
        "description": "Смешные наблюдения о работе, коллегах и профессии",
        "type": "funny"
    },
    {
        "name": "Самоирония",
        "description": "Умение посмеяться над собой и своими недостатками",
        "type": "funny"
    },
    {
        "name": "Остроумные наблюдения",
        "description": "Колкие, умные и остроумные замечания о людях и жизни",
        "type": "funny"
    },
    {
        "name": "Цитаты создателя приложения",
        "description": "Накопленный жизненный опыт",
        "type": "motivation"
    },
]
    
    created_categories = {}
    
    for cat_data in categories_data:
        try:
            category = Category.get(Category.name == cat_data["name"])
            logger.info(f"Категория '{cat_data['name']}' уже существует")
        except Category.DoesNotExist:
            category = Category.create(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            logger.info(f"✅ Создана категория: '{cat_data['name']}'")
        
        created_categories[cat_data["name"]] = category
    
    return created_categories


def move_author_quotes_to_special_category():
    """Переносит все цитаты автора 'Руслан Оноприенко' в специальную категорию"""
    try:
        # Получаем категорию "Цитаты создателя приложения"
        try:
            special_category = Category.get(Category.name == "Цитаты создателя приложения")
        except Category.DoesNotExist:
            logger.warning("Категория 'Цитаты создателя приложения' не найдена")
            return 0
        
        # Варианты написания имени автора
        author_variants = [
            "Руслан Оноприенко",
            "Руслан Оноприенко (Автор приложения)",
            "Руслан Оноприенко (автор приложения)",
            "Оноприенко Р. А.",
            "Ruslan Onopriienko"
        ]
        
        moved_count = 0
        
        # Проверяем мотивационные цитаты
        for quote in Motivation.select().where(Motivation.is_deleted == False):
            if quote.author and any(variant.lower() in quote.author.lower() for variant in author_variants):
                # Проверяем, есть ли уже такая цитата в категории
                existing = CategoryQuote.select().where(
                    (CategoryQuote.category == special_category.id) &
                    (CategoryQuote.quote_text == quote.text) &
                    (CategoryQuote.quote_type == 'motivation')
                ).first()
                
                if not existing:
                    CategoryQuote.create(
                        category=special_category.id,
                        quote_type='motivation',
                        quote_text=quote.text,
                        quote_author=quote.author,
                        added_by='system'
                    )
                    moved_count += 1
                    logger.info(f"Добавлена цитата автора в спецкатегорию: {quote.text[:50]}...")
        
        # Проверяем аффирмации
        for quote in Affirmation.select().where(Affirmation.is_deleted == False):
            if quote.author and any(variant.lower() in quote.author.lower() for variant in author_variants):
                existing = CategoryQuote.select().where(
                    (CategoryQuote.category == special_category.id) &
                    (CategoryQuote.quote_text == quote.text) &
                    (CategoryQuote.quote_type == 'affirmation')
                ).first()
                
                if not existing:
                    CategoryQuote.create(
                        category=special_category.id,
                        quote_type='affirmation',
                        quote_text=quote.text,
                        quote_author=quote.author,
                        added_by='system'
                    )
                    moved_count += 1
        
        # Проверяем юмористические цитаты
        for quote in FunnyQuote.select().where(FunnyQuote.is_deleted == False):
            if quote.author and any(variant.lower() in quote.author.lower() for variant in author_variants):
                existing = CategoryQuote.select().where(
                    (CategoryQuote.category == special_category.id) &
                    (CategoryQuote.quote_text == quote.text) &
                    (CategoryQuote.quote_type == 'funny')
                ).first()
                
                if not existing:
                    CategoryQuote.create(
                        category=special_category.id,
                        quote_type='funny',
                        quote_text=quote.text,
                        quote_author=quote.author,
                        added_by='system'
                    )
                    moved_count += 1
        
        return moved_count
        
    except Exception as e:
        logger.error(f"Ошибка при переносе цитат автора: {e}")
        return 0


class QuoteCategorizer:
    """Класс для умной категоризации цитат без дублирования"""
    
    def __init__(self, categories):
        self.categories = categories
        self.used_quotes = set()
        
    def categorize_motivation(self, quote):
        """Определить ОДНУ категорию для мотивационной цитаты"""
        text = quote.text.lower()
        author = quote.author.lower() if quote.author else ""
    
        quote_key = (quote.text, 'motivation')
        if quote_key in self.used_quotes:
            return None
        self.used_quotes.add(quote_key)
        
        author_mapping = {
            "стив джобс": ["Успех и достижения", "Саморазвитие и рост"],
            "уинстон черчилль": ["Успех и достижения", "Преодоление трудностей"],
            "наполеон хилл": ["Успех и достижения", "Дисциплина и настойчивость"],
            "махатма ганди": ["Лидерство и влияние", "Мудрость жизни"],
            "нельсон мандела": ["Лидерство и влияние", "Преодоление трудностей"],
            "альберт эйнштейн": ["Мудрость жизни", "Саморазвитие и рост"],
            "конфуций": ["Мудрость жизни", "Дисциплина и настойчивость"],
            "томас эдисон": ["Дисциплина и настойчивость", "Преодоление трудностей"],
            "зиг зиглар": ["Дисциплина и настойчивость", "Успех и достижения"],
            "джим рон": ["Саморазвитие и рост", "Дисциплина и настойчивость"],
        }
        
        if author in author_mapping:
            return self.categories.get(author_mapping[author][0])
    
        category_keywords = {
            "Успех и достижения": {
                "keywords": ["успех", "достичь", "достигать", "цель", "победа", "великие дела", 
                           "изменить мир", "создать", "возможности", "мечты", "результат"],
                "weight": 1.0
            },
            "Лидерство и влияние": {
                "keywords": ["лидер", "вести", "управлять", "влияние", "люди", "пример", 
                           "вдохновлять", "команда", "вести за собой"],
                "weight": 1.0
            },
            "Саморазвитие и рост": {
                "keywords": ["расти", "развитие", "учиться", "знания", "меняться", "изменения", 
                           "становиться", "лучше", "совершенство", "прогресс", "рост"],
                "weight": 1.0
            },
            "Преодоление трудностей": {
                "keywords": ["страх", "смелость", "мужество", "бойся", "риск", "трудности", 
                           "преодолеть", "падать", "подниматься", "неудача", "проблема"],
                "weight": 1.0
            },
            "Дисциплина и настойчивость": {
                "keywords": ["дисциплина", "настойчивость", "упорство", "продолжать", 
                           "не останавливаться", "терпение", "постоянство", "привычка"],
                "weight": 1.0
            },
            "Мудрость жизни": {
                "keywords": ["мудрость", "философия", "истина", "смысл", "душа", "разум", 
                           "судьба", "жизнь", "время"],
                "weight": 1.0
            },
            "Действие и решимость": {
                "keywords": ["действие", "делать", "начать", "решимость", "решение", 
                           "выбор", "идти", "двигаться", "шаг", "начинать"],
                "weight": 1.0
            }
        }
        
        scores = {}
        for cat_name, data in category_keywords.items():
            score = sum(1 for kw in data["keywords"] if kw in text) * data["weight"]
            if score > 0:
                scores[cat_name] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            return self.categories.get(best_category)
        
        if "жизнь" in text or "судьба" in text:
            return self.categories.get("Мудрость жизни")
        elif "успех" in text or "достиж" in text:
            return self.categories.get("Успех и достижения")
        
        return self.categories.get("Мудрость жизни")
    
    def categorize_affirmation(self, quote):
        """Определить ОДНУ категорию для аффирмации"""
        text = quote.text.lower()
        
        quote_key = (quote.text, 'affirmation')
        if quote_key in self.used_quotes:
            return None
        self.used_quotes.add(quote_key)
        
        category_keywords = {
            "Любовь к себе": ["любовь", "достоин", "уважение", "принимаю", "себя", "ценю", 
                            "уникальн", "талант", "принимать"],
            "Финансовое благополучие": ["деньги", "финанс", "богатств", "изобилие", 
                                       "процветание", "доход", "благосостояние"],
            "Здоровье и энергия": ["здоров", "тело", "энерги", "исцелени", "сила", 
                                  "дыхание", "физическ", "vitality"],
            "Отношения и гармония": ["отношен", "партнер", "любовь", "гармони", "окружа", 
                                    "люди", "дом", "семья"],
            "Внутренний покой": ["покой", "спокойств", "мир", "гармони", "умиротвор", 
                                "доверяю", "отпуска", "прощаю"],
            "Уверенность и сила": ["уверен", "сила", "могу", "способн", "решительн", 
                                  "смел", "достигаю", "цель"],
            "Благодарность и радость": ["благодар", "радост", "счаст", "позитив", 
                                       "улыб", "праздн", "чудес", "вдохнов"]
        }
        
        scores = {}
        for cat_name, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[cat_name] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            return self.categories.get(best_category)
        
        if re.search(r'я\s+(могу|способ)', text):
            return self.categories.get("Уверенность и сила")
        elif "благодар" in text:
            return self.categories.get("Благодарность и радость")
        elif "достоин" in text or "заслуживаю" in text:
            return self.categories.get("Любовь к себе")
        
        return self.categories.get("Любовь к себе")
    
    def categorize_funny(self, quote):
        """Определить ОДНУ категорию для юмористической цитаты"""
        text = quote.text.lower()
        author = quote.author.lower() if quote.author else ""
        
        quote_key = (quote.text, 'funny')
        if quote_key in self.used_quotes:
            return None
        self.used_quotes.add(quote_key)
        
        if author in ["марк твен", "фаина раневская", "вудди аллен", "джером к. джером"]:
            return self.categories.get("Остроумные наблюдения")
        
        category_keywords = {
            "Жизненная ирония": ["жизнь", "ирония", "парадокс", "странно", "логика", 
                               "справедлив", "вселенная", "судьба"],
            "Лень и прокрастинация": ["лень", "ленив", "прокрастин", "откладыва", 
                                      "ничего не делаю", "бездель", "потом", "завтра"],
            "Возраст и старение": ["возраст", "старый", "молод", "лет", "взросл", 
                                  "пенси", "старость"],
            "Отношения и быт": ["женщин", "мужчин", "отношен", "семья", "брак", 
                               "любовь", "свидан", "жена", "муж"],
            "Работа и карьера": ["работа", "карьер", "начальник", "коллег", "офис", 
                                "зарплат", "бизнес", "професси"],
            "Самоирония": ["я не", "себя", "свой", "свои", "сам", "лично", "мой"],
            "Остроумные наблюдения": ["глупость", "ум", "интеллект", "образование", 
                                      "знание", "понимание", "мыслить"]
        }
        
        scores = {}
        for cat_name, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[cat_name] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            return self.categories.get(best_category)
        
        if "лень" in text or "прокрастин" in text:
            return self.categories.get("Лень и прокрастинация")
        elif "возраст" in text or "стар" in text:
            return self.categories.get("Возраст и старение")
        elif text.startswith("я "):
            return self.categories.get("Самоирония")
        
        return self.categories.get("Жизненная ирония")


def distribute_all_quotes():
    """Главная функция распределения всех цитат (НЕ УДАЛЯЕТ существующие связи)"""
    print("\n" + "="*70)
    print("🚀 РАСПРЕДЕЛЕНИЕ ЦИТАТ ПО КАТЕГОРИЯМ")
    print("="*70)
    
    try:
        db.connect()
        
        print("\n📂 Создание категорий...")
        categories = create_categories()
        print(f"✅ Доступно категорий: {len(categories)}")
        
        # ПЕРВЫЙ ШАГ: Переносим цитаты автора в специальную категорию
        print("\n📝 Перенос цитат создателя приложения в спецкатегорию...")
        moved_count = move_author_quotes_to_special_category()
        print(f"✅ Перенесено цитат: {moved_count}")
        

        print("\n📊 Существующие связи в БД...")
        existing_links = set()
        for link in CategoryQuote.select():
            key = (link.quote_text, link.quote_type)
            existing_links.add(key)
        print(f"✅ Существующих связей: {len(existing_links)}")
        
        categorizer = QuoteCategorizer(categories)
        
        stats = {
            'motivation': {'total': 0, 'new': 0, 'existing': 0},
            'affirmation': {'total': 0, 'new': 0, 'existing': 0},
            'funny': {'total': 0, 'new': 0, 'existing': 0}
        }
        
        # Получаем ID спецкатегории, чтобы пропускать её при обычном распределении
        special_category_id = None
        try:
            special_cat = Category.get(Category.name == "Цитаты создателя приложения")
            special_category_id = special_cat.id
        except Category.DoesNotExist:
            pass
        
        # Распределяем мотивационные цитаты (только новые, и не из спецкатегории)
        print("\n📊 Распределение мотивационных цитат...")
        motivations = Motivation.select().where(Motivation.is_deleted == False)
        stats['motivation']['total'] = motivations.count()
        
        for quote in motivations:
            key = (quote.text, 'motivation')
            
            # Проверяем, не принадлежит ли цитата автору (она уже в спецкатегории)
            is_author_quote = False
            if quote.author:
                author_variants = ["Руслан Оноприенко", "Руслан Оноприенко (Автор приложения)", "Оноприенко"]
                if any(variant.lower() in quote.author.lower() for variant in author_variants):
                    is_author_quote = True
            
            if is_author_quote:
                stats['motivation']['existing'] += 1
                continue
            
            if key in existing_links:
                stats['motivation']['existing'] += 1
                continue
            
            category = categorizer.categorize_motivation(quote)
            if category and category.id != special_category_id:
                CategoryQuote.create(
                    category=category.id,
                    quote_type='motivation',
                    quote_text=quote.text,
                    quote_author=quote.author if quote.author else ""
                )
                existing_links.add(key)
                stats['motivation']['new'] += 1
        
        print(f"   Итого: {stats['motivation']['total']}")
        print(f"   ├─ Уже были: {stats['motivation']['existing']}")
        print(f"   └─ Добавлено новых: {stats['motivation']['new']}")
        
        # Распределяем аффирмации (аналогично)
        print("\n📊 Распределение аффирмаций...")
        affirmations = Affirmation.select().where(Affirmation.is_deleted == False)
        stats['affirmation']['total'] = affirmations.count()
        
        for quote in affirmations:
            key = (quote.text, 'affirmation')
            
            is_author_quote = False
            if quote.author:
                author_variants = ["Руслан Оноприенко", "Руслан Оноприенко (Автор приложения)", "Оноприенко"]
                if any(variant.lower() in quote.author.lower() for variant in author_variants):
                    is_author_quote = True
            
            if is_author_quote:
                stats['affirmation']['existing'] += 1
                continue
            
            if key in existing_links:
                stats['affirmation']['existing'] += 1
                continue
            
            category = categorizer.categorize_affirmation(quote)
            if category and category.id != special_category_id:
                CategoryQuote.create(
                    category=category.id,
                    quote_type='affirmation',
                    quote_text=quote.text,
                    quote_author=quote.author if quote.author else ""
                )
                existing_links.add(key)
                stats['affirmation']['new'] += 1
        
        print(f"   Итого: {stats['affirmation']['total']}")
        print(f"   ├─ Уже были: {stats['affirmation']['existing']}")
        print(f"   └─ Добавлено новых: {stats['affirmation']['new']}")
        
        # Распределяем юмористические цитаты (аналогично)
        print("\n📊 Распределение юмористических цитат...")
        funny = FunnyQuote.select().where(FunnyQuote.is_deleted == False)
        stats['funny']['total'] = funny.count()
        
        for quote in funny:
            key = (quote.text, 'funny')
            
            is_author_quote = False
            if quote.author:
                author_variants = ["Руслан Оноприенко", "Руслан Оноприенко (Автор приложения)", "Оноприенко"]
                if any(variant.lower() in quote.author.lower() for variant in author_variants):
                    is_author_quote = True
            
            if is_author_quote:
                stats['funny']['existing'] += 1
                continue
            
            if key in existing_links:
                stats['funny']['existing'] += 1
                continue
            
            category = categorizer.categorize_funny(quote)
            if category and category.id != special_category_id:
                CategoryQuote.create(
                    category=category.id,
                    quote_type='funny',
                    quote_text=quote.text,
                    quote_author=quote.author if quote.author else ""
                )
                existing_links.add(key)
                stats['funny']['new'] += 1
        
        print(f"   Итого: {stats['funny']['total']}")
        print(f"   ├─ Уже были: {stats['funny']['existing']}")
        print(f"   └─ Добавлено новых: {stats['funny']['new']}")
        
        # Синхронизируем с файлом
        sync_categories_to_file()
        sync_quotes_to_categories_file()
        
        show_final_statistics(categories, stats)
        
        print("\n✨ Распределение завершено успешно!")
        print("📌 Цитаты создателя приложения перенесены в отдельную категорию")
        print("📌 Существующие цитаты в категориях сохранены")
        print("✅ Добавлены только новые цитаты")
        
    except Exception as e:
        logger.error(f"Ошибка при распределении: {e}")
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def show_final_statistics(categories, stats):
    """Показать подробную статистику распределения"""
    print("\n" + "="*70)
    print("📊 СТАТИСТИКА РАСПРЕДЕЛЕНИЯ ПО КАТЕГОРИЯМ")
    print("="*70)
    
    print("\n📁 ПО КАТЕГОРИЯМ:")
    print("-" * 50)
    
    total_in_categories = 0
    
    for cat_name, category in categories.items():
        quotes = CategoryQuote.select().where(CategoryQuote.category == category.id)
        count = quotes.count()
        total_in_categories += count
        
        if count > 0:
            mot = sum(1 for q in quotes if q.quote_type == 'motivation')
            aff = sum(1 for q in quotes if q.quote_type == 'affirmation')
            fun = sum(1 for q in quotes if q.quote_type == 'funny')
            
            if mot > aff and mot > fun:
                icon = "💪"
            elif aff > mot and aff > fun:
                icon = "🌸"
            else:
                icon = "😄"
                
            print(f"{icon} {cat_name}: {count} цитат")
            if mot > 0:
                print(f"   ├─ Мотивация: {mot}")
            if aff > 0:
                print(f"   ├─ Аффирмации: {aff}")
            if fun > 0:
                print(f"   └─ Юмор: {fun}")
    
    print("\n" + "="*70)
    print("📈 ОБЩАЯ СТАТИСТИКА:")
    print("-" * 50)
    
    total_all = stats['motivation']['total'] + stats['affirmation']['total'] + stats['funny']['total']
    total_new = stats['motivation']['new'] + stats['affirmation']['new'] + stats['funny']['new']
    total_existing = stats['motivation']['existing'] + stats['affirmation']['existing'] + stats['funny']['existing']
    
    print(f"Всего цитат в базе: {total_all}")
    print(f"  ├─ Мотивация: {stats['motivation']['total']}")
    print(f"  ├─ Аффирмации: {stats['affirmation']['total']}")
    print(f"  └─ Юмор: {stats['funny']['total']}")
    
    print(f"\nРезультат:")
    print(f"  ├─ Уже были в категориях: {total_existing}")
    print(f"  └─ Добавлено новых: {total_new}")
    print(f"  └─ Всего в категориях: {total_existing + total_new}")
    
    print("\n🔍 ПРОВЕРКА НА ДУБЛИРОВАНИЕ:")
    print("-" * 50)
    
    all_quotes = list(CategoryQuote.select())
    quote_keys = [(q.quote_text, q.quote_type) for q in all_quotes]
    unique_keys = set(quote_keys)
    
    if len(quote_keys) == len(unique_keys):
        print("✅ Дубликатов не найдено!")
    else:
        duplicates = len(quote_keys) - len(unique_keys)
        print(f"⚠️ Найдено дубликатов: {duplicates}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    distribute_all_quotes()

# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)


# Категории с цитатами (автоматически синхронизировано)
CATEGORY_QUOTES = {
    "Цитаты создателя приложения": [
        {
            "text": "В людях нет ничего человеческого - они родную мать готовы продать в случае опасности",
            "author": "Руслан Оноприенко (автор приложения)",
            "type": "motivation"
        },
    ],
    "Успех и достижения": [
    ],
    "Действие и решимость": [
    ],
    "Саморазвитие и рост": [
    ],
    "Мудрость жизни": [
    ],
    "Лидерство и влияние": [
    ],
    "Дисциплина и настойчивость": [
    ],
    "Преодоление трудностей": [
    ],
    "Любовь к себе": [
    ],
    "Финансовое благополучие": [
    ],
    "Благодарность и радость": [
    ],
    "Уверенность и сила": [
    ],
    "Здоровье и энергия": [
    ],
    "Внутренний покой": [
    ],
    "Отношения и гармония": [
    ],
    "Самоирония": [
    ],
    "Жизненная ирония": [
    ],
    "Остроумные наблюдения": [
    ],
    "Лень и прокрастинация": [
    ],
    "Отношения и быт": [
    ],
    "Возраст и старение": [
    ],
    "Работа и карьера": [
    ],
}

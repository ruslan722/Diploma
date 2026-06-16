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
        
        # Получаем существующие связи, НЕ УДАЛЯЕМ их!
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
CATEGORY_QUOTES = {
    "Цитаты создателя приложения": [
        {
            "text": "Живите ради себя, а не одобрения других людей,  тогда вы будете счастливы",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "За 23 года я понял что люди особо от животных не отличаются, хотя мне пытались доказать обратное",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "Единственный ваш друг - вы сами",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "Войны - самая бесполезная трата  времени и ресурсов.",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "Люди это нечто - способное свернуть все ради своей цели",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "Мало людей которые готовы услышать правду им нужна ваша ложь",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "В людях нет ничего человеческого - они и мать родную продадут если им это выгодно",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "motivation"
        },
        {
            "text": "Задача крепкого и сильного мужчины строить империи, а не служить женщине. Прчему мы не туда свернули?",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "funny"
        },
        {
            "text": "Иногда мне кажется что все что я прошел было в цирке",
            "author": "Руслан Оноприенко (Автор приложения)",
            "type": "funny"
        },
        {
            "text": "В людях нет ничего человеческого - они родную мать готовы продать в случае опасности",
            "author": "Руслан Оноприенко (автор приложения)",
            "type": "motivation"
        },
    ],
    "Успех и достижения": [
        {
            "text": "Люди, которые достаточно сумасшедшие, чтобы думать, что они могут изменить мир — это те, кто действительно на это способен.",
            "author": "Стив Джобс",
            "type": "motivation"
        },
        {
            "text": "Успех не окончателен, неудача не фатальна: главное — иметь мужество продолжать.",
            "author": "Уинстон Черчилль",
            "type": "motivation"
        },
        {
            "text": "Лучший способ предсказать будущее — создать его.",
            "author": "Питер Друкер",
            "type": "motivation"
        },
        {
            "text": "Возможности не приходят сами — вы создаете их.",
            "author": "Крис Гроссер",
            "type": "motivation"
        },
        {
            "text": "Единственный способ делать великие дела — любить то, что вы делаете.",
            "author": "Стив Джобс",
            "type": "motivation"
        },
        {
            "text": "Успех — это способность двигаться от неудачи к неудаче, не теряя энтузиазма.",
            "author": "Уинстон Черчилль",
            "type": "motivation"
        },
        {
            "text": "Ваше время ограничено, не тратьте его, живя чужой жизнью.",
            "author": "Стив Джобс",
            "type": "motivation"
        },
        {
            "text": "Имейте смелость следовать зову своего сердца и интуиции.",
            "author": "Стив Джобс",
            "type": "motivation"
        },
        {
            "text": "Что разум человека может постигнуть и во что он может поверить, того он способен и достичь.",
            "author": "Наполеон Хилл",
            "type": "motivation"
        },
        {
            "text": "Люди, которые достаточно сумасшедшие, чтобы думать, что могут изменить мир, действительно его меняют.",
            "author": "Робин Уильямс",
            "type": "motivation"
        },
        {
            "text": "Не ждите. Время никогда не будет подходящим.",
            "author": "Наполеон Хилл",
            "type": "motivation"
        },
        {
            "text": "Секрет успеха в том, чтобы начать.",
            "author": "Марк Твен",
            "type": "motivation"
        },
        {
            "text": "Лучшая месть — огромный успех.",
            "author": "Фрэнк Синатра",
            "type": "motivation"
        },
        {
            "text": "Будущее принадлежит тем, кто верит в красоту своей мечты.",
            "author": "Элеонора Рузвельт",
            "type": "motivation"
        },
        {
            "text": "Единственное, что стоит между вами и вашей целью, — это история, которую вы постоянно рассказываете себе, почему вы не можете ее достичь.",
            "author": "Джордан Белфорт",
            "type": "motivation"
        },
        {
            "text": "Чем тяжелее битва, тем значительнее победа.",
            "author": "Томас Пейн",
            "type": "motivation"
        },
        {
            "text": "Ограничения живут только в нашем сознании. Но если мы используем свое воображение, наши возможности становятся бесконечными.",
            "author": "Джейми Паолинетти",
            "type": "motivation"
        },
        {
            "text": "Успех обычно приходит к тем, кто слишком занят, чтобы его просто ждать.",
            "author": "Генри Дэвид Торо",
            "type": "motivation"
        },
        {
            "text": "Вы никогда не будете слишком стары, чтобы ставить новую цель или мечтать о новой мечте.",
            "author": "К.С. Льюис",
            "type": "motivation"
        },
        {
            "text": "Неудача — это приправа, которая придает успеху его вкус.",
            "author": "Труман Капоте",
            "type": "motivation"
        },
        {
            "text": "Развивайте успех из неудач. Разочарование и неудача — два самых верных шага к успеху.",
            "author": "Дейл Карнеги",
            "type": "motivation"
        },
        {
            "text": "Чтобы добиться успеха, ваше желание успеха должно быть больше, чем ваш страх неудачи.",
            "author": "Билл Косби",
            "type": "motivation"
        },
        {
            "text": "Качество — это не случайность; это всегда результат разумного усилия.",
            "author": "Джон Раскин",
            "type": "motivation"
        },
        {
            "text": "Ваша работа заполнит большую часть вашей жизни, и единственный способ быть truly удовлетворенным — это делать то, что вы считаете великой работой.",
            "author": "Стив Джобс",
            "type": "motivation"
        },
        {
            "text": "Успех — это не ключ к счастью. Счастье — это ключ к успеху.",
            "author": "Альберт Швейцер",
            "type": "motivation"
        },
        {
            "text": "Ничто не может помешать человеку с правильным mental attitude от достижения своей цели.",
            "author": "Томас Джефферсон",
            "type": "motivation"
        },
        {
            "text": "Если вы не видите себя богатым, вы никогда не станете богатым.",
            "author": "Наполеон Хилл",
            "type": "motivation"
        },
        {
            "text": "Все, что человеческий разум может conceive и верить, он может достичь.",
            "author": "Наполеон Хилл",
            "type": "motivation"
        },
        {
            "text": "Единственное место, где успех приходит до работы, — это словарь.",
            "author": "Виддал Браун",
            "type": "motivation"
        },
        {
            "text": "Если вы не можете делать великие вещи, делайте маленькие вещи великим образом.",
            "author": "Наполеон Хилл",
            "type": "motivation"
        },
        {
            "text": "Путь к успеху — это действие.",
            "author": "Александр Дюма",
            "type": "motivation"
        },
    ],
    "Действие и решимость": [
        {
            "text": "В любой момент у нас есть два варианта: сделать шаг вперёд к росту или вернуться в безопасное место.",
            "author": "Абрахам Маслоу",
            "type": "motivation"
        },
        {
            "text": "Сложнее всего начать действовать, все остальное зависит только от упорства.",
            "author": "Амелия Эрхарт",
            "type": "motivation"
        },
        {
            "text": "Самый лучший способ взяться за что-то — перестать говорить и начать делать.",
            "author": "Уолт Дисней",
            "type": "motivation"
        },
        {
            "text": "Не смотри на часы; делай то, что оно делает. Продолжай идти.",
            "author": "Сэм Левенсон",
            "type": "motivation"
        },
        {
            "text": "Чем больше я хочу что-то сделать, тем меньше я называю это работой.",
            "author": "Ричард Бах",
            "type": "motivation"
        },
        {
            "text": "Будьте несчастны. Или мотивируйте себя. Что бы ни случилось, это всегда ваш выбор.",
            "author": "Уэйн Дайер",
            "type": "motivation"
        },
    ],
    "Саморазвитие и рост": [
        {
            "text": "Выживает не самый сильный из видов и не самый умный, а тот, кто лучше других реагирует на изменения.",
            "author": "Чарльз Дарвин",
            "type": "motivation"
        },
        {
            "text": "Прогресс невозможен без изменений, и те, кто не может изменить своё мнение, не могут изменить ничего вообще.",
            "author": "Джордж Бернард Шоу",
            "type": "motivation"
        },
        {
            "text": "Знания — это сила.",
            "author": "Фрэнсис Бэкон",
            "type": "motivation"
        },
        {
            "text": "Есть только один уголок вселенной, в котором вы можете быть уверены в улучшении, и это ваша собственная личность.",
            "author": "Олдос Хаксли",
            "type": "motivation"
        },
        {
            "text": "Если вы не готовы рискнуть обычным, вам придется довольствоваться обычным.",
            "author": "Джим Рон",
            "type": "motivation"
        },
        {
            "text": "Даже если вы на правильном пути, вас собьют, если вы будете просто сидеть на месте.",
            "author": "Уилл Роджерс",
            "type": "motivation"
        },
        {
            "text": "Определенные цветы растут только в темноте. Некоторые симфонии создаются только в тишине. Ваше лучшее «я» может проявиться только в трудностях.",
            "author": "Морган Харпер Николс",
            "type": "motivation"
        },
        {
            "text": "Я бы предпочел умереть от страсти, чем от скуки.",
            "author": "Винсент Ван Гог",
            "type": "motivation"
        },
        {
            "text": "Независимо от того, насколько вы хороши, вы всегда можете стать лучше, и это exciting вызов.",
            "author": "Тайгер Вудс",
            "type": "motivation"
        },
        {
            "text": "Мотивация — это то, с чего вы начинаете. Привычка — это то, что keeps вас идущим.",
            "author": "Джим Рон",
            "type": "motivation"
        },
        {
            "text": "Для них ты просто псих, как я. Сейчас ты им нужен, а надоешь — они тебя выкинут, как прокажённого. Их принципы, их кодекс — всего лишь слова, забываемые при первой опасности. Они такие, какими мир позволяет им быть.",
            "author": "Джокер (Хитт Ленджер)",
            "type": "motivation"
        },
    ],
    "Мудрость жизни": [
        {
            "text": "Секрет перемен состоит в том, чтобы сосредоточитьсся на создании нового, а не на борьбе со старым.",
            "author": "Сократ",
            "type": "motivation"
        },
        {
            "text": "Жизнь — как езда на велосипеде: чтобы сохранить равновесие, нужно продолжать движение.",
            "author": "Альберт Эйнштейн",
            "type": "motivation"
        },
        {
            "text": "Неважно, насколько медленно вы идёте, если не останавливаетесь.",
            "author": "Конфуций",
            "type": "motivation"
        },
        {
            "text": "Не бойтесь отказываться от хорошего в пользу великого.",
            "author": "Джон Д. Рокфеллер",
            "type": "motivation"
        },
        {
            "text": "Наша судьба в небесах, а не в звездах.",
            "author": "Уильям Шекспир",
            "type": "motivation"
        },
        {
            "text": "Вы не можете пересечь океан, пока не наберетесь смелости потерять берег из виду.",
            "author": "Христофор Колумб",
            "type": "motivation"
        },
        {
            "text": "Если вы думаете, что вы слишком малы, чтобы что-то изменить, попробуйте спать с комаром.",
            "author": "Далай-лама",
            "type": "motivation"
        },
        {
            "text": "Мы становимся тем, о чем мы думаем.",
            "author": "Эрл Найтингейл",
            "type": "motivation"
        },
        {
            "text": "Жизнь — это не ожидание, когда утихнет буря, а обучение танцу под дождем.",
            "author": "Вивиан Грин",
            "type": "motivation"
        },
        {
            "text": "Если нет ветра, беритесь за вёсла.",
            "author": "Латинская пословица",
            "type": "motivation"
        },
        {
            "text": "Не позволяйте вчерашнему дню отнимать слишком много сегодняшнего.",
            "author": "Уилл Роджерс",
            "type": "motivation"
        },
        {
            "text": "Мечтатели — это спасители мира.",
            "author": "Джеймс Аллен",
            "type": "motivation"
        },
        {
            "text": "Единственное настоящее богатство — это талант.",
            "author": "Стендаль",
            "type": "motivation"
        },
        {
            "text": "Все, что вы можете вообразить, реально.",
            "author": "Пабло Пикассо",
            "type": "motivation"
        },
        {
            "text": "Вы должны выучить правила игры. А затем вы должны играть лучше, чем кто-либо другой.",
            "author": "Альберт Эйнштейн",
            "type": "motivation"
        },
        {
            "text": "Великие умы обсуждают идеи; средние умы обсуждают события; маленькие умы обсуждают людей.",
            "author": "Элеонора Рузвельт",
            "type": "motivation"
        },
        {
            "text": "Я не продукт своих обстоятельств. Я продукт своих решений.",
            "author": "Стивен Кови",
            "type": "motivation"
        },
        {
            "text": "Когда кажется, что все идет против вас, помните, что самолет взлетает против ветра, а не по ветру.",
            "author": "Генри Форд",
            "type": "motivation"
        },
        {
            "text": "Не идите туда, куда ведет путь. Идите вместо этого там, где нет пути, и оставьте след.",
            "author": "Ральф Уолдо Эмерсон",
            "type": "motivation"
        },
        {
            "text": "Каждый художник сначала был любителем.",
            "author": "Ральф Уолдо Эмерсон",
            "type": "motivation"
        },
        {
            "text": "Чтобы быть незаменимым, нужно всегда быть разным.",
            "author": "Коко Шанель",
            "type": "motivation"
        },
        {
            "text": "Вы можете столкнуться со многими поражениями, но вы не должны быть побеждены.",
            "author": "Майя Энджелоу",
            "type": "motivation"
        },
        {
            "text": "Никогда не прерывайте своего врага, когда он совершает ошибку.",
            "author": "Наполеон Бонапарт",
            "type": "motivation"
        },
        {
            "text": "Мы должны верить, что мы одарены чем-то, и что это должно быть достигнуто.",
            "author": "Мария Кюри",
            "type": "motivation"
        },
        {
            "text": "Ум — это все. Вы становитесь тем, о чем думаете.",
            "author": "Будда",
            "type": "motivation"
        },
        {
            "text": "Если вы предлагаете что-то, во что вы действительно верите, вам не нужно быть убедительным.",
            "author": "Сет Годин",
            "type": "motivation"
        },
        {
            "text": "Тот, кто имеет зачем жить, может вынести почти любое как.",
            "author": "Фридрих Ницше",
            "type": "motivation"
        },
        {
            "text": "Я предпочитаю быть правым оптимистом, а не правым пессимистом.",
            "author": "Бертран Рассел",
            "type": "motivation"
        },
        {
            "text": "Чем больше вы хвалите и празднуете свою жизнь, тем больше в жизни есть что праздновать.",
            "author": "Опра Уинфри",
            "type": "motivation"
        },
        {
            "text": "Жизнь — это не поиск себя. Жизнь — это создание себя.",
            "author": "Джордж Бернард Шоу",
            "type": "motivation"
        },
        {
            "text": "Если вы не можете объяснить это просто, вы не понимаете это достаточно хорошо.",
            "author": "Альберт Эйнштейн",
            "type": "motivation"
        },
        {
            "text": "Чем больше я тренируюсь, тем больше мне везет.",
            "author": "Гэри Плейер",
            "type": "motivation"
        },
        {
            "text": "Я ненавидел каждую minute тренировок, но я сказал: «Не бросай. Страдай сейчас и живи остаток своей жизни как чемпион».",
            "author": "Мухаммед Али",
            "type": "motivation"
        },
        {
            "text": "Не бойтесь совершенства; вы никогда его не достигнете.",
            "author": "Сальвадор Дали",
            "type": "motivation"
        },
        {
            "text": "Иногда вы можете обманывать всех, и даже самого себя, но вы не можете обманывать свое сердце.",
            "author": "Пауло Коэльо",
            "type": "motivation"
        },
        {
            "text": "Одиночество - это когда дома есть телефон, а звонит только будильник.",
            "author": "Фаина Георгиевна Раневская",
            "type": "motivation"
        },
        {
            "text": "Я верю, что то, что тебя не убивает, делает тебя… страннее!",
            "author": "Джокер (Хитт Леджер)",
            "type": "motivation"
        },
        {
            "text": "Трудные времена не создают героев. Именно в трудные времена раскрывается герой внутри нас.",
            "author": "Роберт Ренфро Райли",
            "type": "motivation"
        },
        {
            "text": "Легка жизнь только дуракам",
            "author": "Неизвестно",
            "type": "motivation"
        },
        {
            "text": "Самая большая ошибка, которую ты можешь совершить в жизни  - бояться совершить ошибку",
            "author": "Эльберт Хаббард",
            "type": "motivation"
        },
        {
            "text": "В этой жизни есть 2 типа людей - крысы которые тянут на дно и те кто им потакает",
            "author": "Неизвестный",
            "type": "motivation"
        },
    ],
    "Лидерство и влияние": [
        {
            "text": "Если ты хочешь перемену в будущем, стань этой переменой в настоящем.",
            "author": "Махатма Ганди",
            "type": "motivation"
        },
        {
            "text": "Величайшая слава в жизни заключается не в падении, а в том, чтобы подниматься каждый раз, когда мы падаем.",
            "author": "Нельсон Мандела",
            "type": "motivation"
        },
        {
            "text": "Это всегда кажется невозможным, пока это не сделано.",
            "author": "Нельсон Мандела",
            "type": "motivation"
        },
        {
            "text": "Лучший способ найти себя — это потерять себя в служении другим.",
            "author": "Махатма Ганди",
            "type": "motivation"
        },
        {
            "text": "Лидер — это тот, кто знает путь, идет путем и показывает путь.",
            "author": "Джон К. Максвелл",
            "type": "motivation"
        },
        {
            "text": "Сила не приходит от физических возможностей. Она приходит от несгибаемой воли.",
            "author": "Махатма Ганди",
            "type": "motivation"
        },
        {
            "text": "Чтобы вести людей, идите behind них.",
            "author": "Лао-цзы",
            "type": "motivation"
        },
        {
            "text": "Инвестиция в знания приносит наибольшие дивиденды.",
            "author": "Бенджамин Франклин",
            "type": "motivation"
        },
        {
            "text": "Сначала они игнорируют вас, затем смеются над вами, затем борются с вами, а затем вы побеждаете.",
            "author": "Махатма Ганди",
            "type": "motivation"
        },
    ],
    "Дисциплина и настойчивость": [
        {
            "text": "Я не потерпел неудачу. Я просто нашел 10 000 способов, которые не работают.",
            "author": "Томас Эдисон",
            "type": "motivation"
        },
        {
            "text": "Три самых главных слова для успеха: желание, дисциплина и настойчивость.",
            "author": "Роберт Кийосаки",
            "type": "motivation"
        },
        {
            "text": "Наш greatest слабость lies в giving up. Самый верный способ добиться успеха — это попробовать еще один раз.",
            "author": "Томас Эдисон",
            "type": "motivation"
        },
        {
            "text": "Люди часто говорят, что мотивация длится недолго. Ну, и bathing тоже — поэтому мы рекомендуем его ежедневно.",
            "author": "Зиг Зиглар",
            "type": "motivation"
        },
        {
            "text": "Нет лифта к успеху. Вы должны подняться по лестнице.",
            "author": "Зиг Зиглар",
            "type": "motivation"
        },
    ],
    "Преодоление трудностей": [
        {
            "text": "Трудности готовят обычных людей к необычной судьбе.",
            "author": "К.С. Льюис",
            "type": "motivation"
        },
        {
            "text": "Мир принадлежит тем, кто имеет мужество мечтать и смелость действовать.",
            "author": "А.П.Дж. Абдул Калам",
            "type": "motivation"
        },
        {
            "text": "Смелость — это сопротивление страху, mastery страха, а не отсутствие страха.",
            "author": "Марк Твен",
            "type": "motivation"
        },
        {
            "text": "Вы получаете от жизни то, что имеете смелость просить.",
            "author": "Опра Уинфри",
            "type": "motivation"
        },
    ],
    "Любовь к себе": [
        {
            "text": "Я достойна любви и уважения",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю успеха",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю отношения, наполненные уважением, нежностью и доверием",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое тело — мой союзник, я забочусь о нем с любовью",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я справляюсь с любыми ситуациями",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я верю в себя и свои решения",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои мысли создают мою реальность",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я привлекаю в свою жизнь только хороших людей",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Каждый день я становлюсь лучше",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое сердце открыто для любви",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я прощаю себя и других",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои мечты сбываются легко и effortlessly",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю жизнь своей мечты",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Вселенная всегда поддерживает меня",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя душа излучает свет",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я принимаю себя полностью и без условий",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Каждый день приносит новые возможности",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое воображение безгранично",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю отдыха и заботы о себе",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои таланты уникальны и ценны",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое сердце знает правильный путь",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои слова имеют силу и значение",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мой разум ясен и сосредоточен",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я привлекаю возможности для роста",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое прошлое не определяет мое будущее",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я легко нахожу решения любых проблем",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я излучаю любовь и принимаю любовь",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю время для себя",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я открыта для новых идей",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя интуиция всегда ведет меня верно",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю гармонию вокруг себя",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои мечты важны и реализуемы",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои цели ясны и достижимы",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю процветания",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я выбираю мысли, которые исцеляют",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое присутствие успокаивает других",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я легко адаптируюсь к изменениям",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за свою уникальность",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои решения мудры и своевременны",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю уважения и признания",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое будущее яркое и прекрасное",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я легко выражаю свои чувства",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое тело знает, как исцелить себя",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я выбираю путь легкости и flow",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я достойна всего самого лучшего",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю свой собственный успех",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои мечты реализуются в идеальное время",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я заслуживаю любви именно сейчас",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя жизнь становится лучше с каждым днем",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои действия согласованы с моими ценностями",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я выбираю любовь вместо страха",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя душа вечна и прекрасна",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Воин никогда не умрет",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Финансовое благополучие": [
        {
            "text": "Деньги приходят ко мне легко и в изобилии",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я открыта финансовому потоку и достойна богатства",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Изобилие — мое естественное состояние",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю изобилие во всех сферах жизни",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои финансы постоянно растут",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я привлекаю изобилие естественно",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Благодарность и радость": [
        {
            "text": "Я благодарна за этот новый день и все, что он мне принесет",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я выбираю мысли, которые наполняют меня радостью",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за все уроки жизни",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я выбираю счастье каждый день",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за каждое мгновение",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои действия вдохновляют других",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я нахожу радость в простых вещах",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за поддержку вселенной",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое сердце полно благодарности",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя жизнь — это праздник",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я привлекаю вдохновляющие события",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя жизнь наполнена чудесами",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за свой внутренний свет",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое сердце открыто для чудес",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои мысли позитивны и созидательны",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за этот момент здесь и сейчас",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я создаю пространство для радости",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Уверенность и сила": [
        {
            "text": "Я достойна успеха и достигаю своих целей",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я смело иду к своим целям",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя жизнь наполнена смыслом и целью",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои творческие способности безграничны",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Моя душа знает свою цель",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за все свои способности",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я могущественен",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Здоровье и энергия": [
        {
            "text": "Я излучаю уверенность и позитивную энергию",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благословляю свое тело здоровьем и vitality",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я благодарна за свое здоровье",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я наполняюсь энергией и энтузиазмом",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое тело исцеляется с каждым днем",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое тело прекрасно таким, какое оно есть",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое дыхание соединяет меня с жизнью",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Внутренний покой": [
        {
            "text": "Я отпускаю все, что больше не служит моему высшему благу",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я доверяю своему внутреннему голосу",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое дыхание наполняет меня спокойствием",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я отпускаю страх и доверяю жизни",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я приношу пользу этому миру",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я легко отпускаю то, что мне не служит",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я доверяю процессу жизни",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мое сердце излучает мир и покой",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я легко прощаю и отпускаю",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я доверяю своей мудрости",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я жив и пусть мир одрогнётся",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Отношения и гармония": [
        {
            "text": "Я живу в гармонии с вселенной",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Любовь окружает меня повсюду",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я достойна прекрасных отношений",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Я привлекаю идеальных партнеров",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мой дом наполнен любовью и светом",
            "author": "",
            "type": "affirmation"
        },
        {
            "text": "Мои отношения гармоничны и радостны",
            "author": "",
            "type": "affirmation"
        },
    ],
    "Самоирония": [
        {
            "text": "Я никогда не позволял, чтобы мои школьные занятия мешали моему образованию.",
            "author": "Эрнест Хемингуэй",
            "type": "funny"
        },
        {
            "text": "В старости некоторые свойства характера утрачиваются, но глупость к их числу не относится.",
            "author": "Хендрик Грун",
            "type": "funny"
        },
        {
            "text": "Я всегда беру с собой в поездку книгу - на случай, если будет скучно. А она всегда бывает скучной.",
            "author": "Гилберт Честертон",
            "type": "funny"
        },
        {
            "text": "Я не суеверный - это приносит неудачу.",
            "author": "Айзек Азимов",
            "type": "funny"
        },
        {
            "text": "Я не боюсь смерти, я просто не хочу там оказаться, когда это случится.",
            "author": "Вуди Аллен",
            "type": "funny"
        },
        {
            "text": "Всегда будь самим собой, если, конечно, ты не можешь быть пиратом. Тогда всегда будь пиратом.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не старею, я становлюсь классиком.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я читал так много книг о вреде курения, что решил бросить... читать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не говорю, что привидений не существует, но я бы хотел, чтобы они платили аренду.",
            "author": "Спиридон Дмитриевич",
            "type": "funny"
        },
        {
            "text": "Я на такой диете, что даже фотографии еды полнеют.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не грубый, я просто прямолинейный. Как поезд, который сбил ваш дом.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда ношу часы, но когда ношу, они показывают, что я опаздываю.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый быстрый способ удвоить свои деньги - сложить их пополам и положить обратно в карман.",
            "author": "Уилл Роджерс",
            "type": "funny"
        },
        {
            "text": "Я не говорю, что я идеален, но я близок к этому.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не сумасшедший, у меня просто эксклюзивное мышление.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Лучший способ не расстраиваться - ожидать худшего с самого начала.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не толстый, я просто легко набираю вес... Очень легко... Слишком легко.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не избегаю ответственности, я просто нахожу более творческие способы ее делегировать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, что делаю, но я делаю это с уверенностью.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый опасный вид невежества - это когда вы не знаете, что чего-то не знаете.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не говорю, что я перфекционист, но если бы я был им, все было бы идеально.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не суеверный, но я немного стеверный.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда прав, но я никогда не ошибаюсь.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый сложный период в жизни - это когда ты уже не ребенок, но еще не взрослый. Или когда ты уже взрослый, но ведешь себя как ребенок.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, куда иду, но я иду туда очень быстро.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю, что происходит, но я всегда делаю вид, что понимаю.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда уверен в себе, но я всегда уверен в своей неуверенности.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый верный способ разбогатеть - это родиться в богатой семье.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, что сказать, но я всегда нахожу, что сказать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда достигаю своих целей, но я всегда достигаю холодильника.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда прав, но мне нравится думать, что я прав.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю шутки, но я всегда смеюсь, когда все смеются.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый сложный язык - это тот, который ты изучал в школе, но так и не выучил.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, что делать, но я всегда знаю, что не делать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда успешен, но я всегда пытаюсь.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю современное искусство, но я всегда киваю с умным видом.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю ответы, но я всегда знаю, где их найти. (В Google)",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый верный способ что-то найти - это перестать это искать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда доволен результатом, но я всегда доволен процессом.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю, почему я что-то делаю, но я всегда нахожу этому оправдание.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда следую инструкциям, но я всегда читаю их после того, как что-то сломаю.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда уверен в своих решениях, но я всегда уверен в их последствиях.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый сложный экзамен в жизни - это экзамен на водительские права. Особенно если ты его сдаешь в пятый раз.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда достигаю совершенства, но я всегда достигаю прогресса.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю, что происходит в мире, но я всегда имею об этом мнение.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда следую плану, но у меня всегда есть план Б. И план В. И план Г...",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, куда иду, но я всегда знаю, откуда пришел.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый верный способ что-то испортить - это попытаться сделать это идеально.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю шутки, но я всегда улыбаюсь, когда все смеются.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда достигаю своих целей, но я всегда достигаю дивана после работы.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда знаю, что правильно, но я всегда знаю, что вкусно.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда следую правилам, но я всегда знаю, когда их нарушаю.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Самый сложный вопрос - это 'что ты хочешь на ужин?'. Особенно если ты его задаешь сам себе.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не всегда понимаю современную музыку, но я всегда подпеваю, когда ее слышу.",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Жизненная ирония": [
        {
            "text": "Две вещи бесконечны: вселенная и человеческая глупость; и я еще не уверен насчет вселенной.",
            "author": "Альберт Эйнштейн",
            "type": "funny"
        },
        {
            "text": "Он любил и страдал. Он любил деньги и страдал от их недостатка.",
            "author": "Илья Ильф и Евгений Петров",
            "type": "funny"
        },
        {
            "text": "Интеллигент совершает те же низости, что и обычный человек, но при этом очень переживает.",
            "author": "Александр Цыпкин",
            "type": "funny"
        },
        {
            "text": "Ничто так не выдает человека, как то, над чем он смеется.",
            "author": "Иоганн Вольфганг Гёте",
            "type": "funny"
        },
        {
            "text": "Если бы строители строили здания так, как программисты пишут программы, первый дятел уничтожил бы цивилизацию.",
            "author": "Артур Кларк",
            "type": "funny"
        },
        {
            "text": "Диета - это единственная игра, в которой вы выигрываете, когда теряете.",
            "author": "Карл Лагерфельд",
            "type": "funny"
        },
        {
            "text": "Если сначала у вас ничего не получается, значит, прыжки с парашютом не для вас.",
            "author": "Стивен Райт",
            "type": "funny"
        },
        {
            "text": "Деньги не могут купить счастье, но они могут купить яхту, чтобы подплыть к нему поближе.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Оптимист верит, что мы живем в лучшем из миров. Пессимист боится, что так оно и есть.",
            "author": "Джеймс Бранч Кабелл",
            "type": "funny"
        },
        {
            "text": "Если бы я хотел услышать твое мнение, я бы спросил у тебя про твою личную жизнь.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы ошибки в жизни давали опыт, я бы уже был гением.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была справедливой, эльфы бы делали всю работу.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы мне платили за каждую сделанную мной ошибку, я бы уже был миллионером.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была легкой, где бы мы брали истории для разговоров?",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была справедливой, мороженое было бы полезным для здоровья.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы у меня был доллар за каждый раз, когда я что-то забываю, я бы... э-э... забыл, что я хотел сказать.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была видеоигрой, я бы искал чит-коды.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была справедливой, понедельники были бы выходными.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была книгой, я бы пропустил скучные главы.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была справедливой, пицца была бы овощем.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы у меня был выбор между славой и анонимностью, я бы выбрал анонимность. Но так, чтобы все об этом знали.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы жизнь была игрой, я бы играл в режиме 'легко'. И все равно проигрывал.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Никогда не упускайте хороший шанс заткнуться.",
            "author": "Уилл Роджерс",
            "type": "funny"
        },
        {
            "text": "Сегодня я понял что моя жизнь это комедия где я актер",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Остроумные наблюдения": [
        {
            "text": "Банкир - это человек, который одалживает вам свой зонтик, когда светит солнце, но хочет вернуть его в ту же минуту, когда начинается дождь.",
            "author": "Марк Твен",
            "type": "funny"
        },
        {
            "text": "В этом сказался весь Гаррис: он так охотно берет на себя всю тяжесть работы и перекладывает ее на плечи других.",
            "author": "Джером К. Джером",
            "type": "funny"
        },
        {
            "text": "Жизнь слишком коротка, чтобы тратить ее на диеты, жадных мужчин и плохое настроение.",
            "author": "Фаина Раневская",
            "type": "funny"
        },
        {
            "text": "Никогда не откладывай на завтра то, что можно сделать послезавтра.",
            "author": "Марк Твен",
            "type": "funny"
        },
        {
            "text": "Если бы у меня был доллар за каждую умную мысль, которая пришла мне в голову, у меня все равно не было бы денег.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы мне платили за то, что я думаю, я бы уже был банкротом.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Воин должен уметь проигрывать иначе когда нибудь сломает свою спину",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Лень и прокрастинация": [
        {
            "text": "Вечно серьезен, потому что лень смеяться.",
            "author": "Антон Чехов",
            "type": "funny"
        },
        {
            "text": "Я не бездельник, я просто люблю ничего не делать.",
            "author": "Сюзи Жуффа",
            "type": "funny"
        },
        {
            "text": "Если женщина о чем-то вас спрашивает - лучше промолчать, потому что она все равно не слушает.",
            "author": "Олег Рой",
            "type": "funny"
        },
        {
            "text": "Я не ленивый, я просто на энергосберегающем режиме.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не прокрастинирую, я просто жду последней минуты, чтобы сделать все сразу.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не ленивый, я в режиме энергосбережения.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не прокрастинатор, я просто жду, пока не наступит подходящий момент для паники.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Я не говорю, что я ленивый, но если бы трудолюбие было инфекцией, я бы был в карантине.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы мне платили за каждую минуту, когда я ничего не делаю, я бы уже был миллионером. О, подождите, я это уже говорил.",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Отношения и быт": [
        {
            "text": "Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему.",
            "author": "Лев Толстой",
            "type": "funny"
        },
        {
            "text": "Если женщина молчит, значит, она либо думает, либо уже все решила.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы у меня был выбор между любовью и шоколадом, я бы выбрал шоколад. По крайней мере, он не предает.",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Возраст и старение": [
        {
            "text": "Возраст - это всего лишь число, но, черт возьми, какое большое число!",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст дает мудрость. И желание вздремнуть.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда вы перестаете говорить 'когда я вырасту' и начинаете говорить 'когда я был молодым'.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Если бы мне платили за сон, я бы уже вышел на пенсию.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда твои сны стоят дороже, чем их исполнение.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда ты понимаешь, что 'рано ложиться спать' - это не наказание, а награда.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда ты предпочитаешь остаться дома в пятницу вечером, и это кажется тебе отличной идеей.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда ты понимаешь, что 'модно' - это то, что удобно.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда ты понимаешь, что 'поздно' - это 9 вечера.",
            "author": "Неизвестный",
            "type": "funny"
        },
        {
            "text": "Возраст - это когда ты понимаешь, что 'вечеринка' - это когда ты ложишься спать до 10 вечера.",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
    "Работа и карьера": [
        {
            "text": "Если бы у меня был выбор между работой и отдыхом, я бы выбрал отдых. Но сначала немного поработал бы.",
            "author": "Неизвестный",
            "type": "funny"
        },
    ],
}

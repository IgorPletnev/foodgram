import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к JSON-файлу с ингредиентами',
        )

    def handle(self, *args, **options):
        file_path = options.get('path')
        if not file_path:
            base_dir = settings.BASE_DIR.parent
            file_path = os.path.join(base_dir, 'data', 'ingredients.json')
            if not os.path.exists(file_path):
                file_path = os.path.join(
                    settings.BASE_DIR,
                    'data',
                    'ingredients.json',
                )
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as json_file:
            ingredients_data = json.load(json_file)

        total_count = len(ingredients_data)
        ingredients_to_create = []
        skipped = 0
        for ingredient_item in ingredients_data:
            name = ingredient_item.get('name')
            unit = ingredient_item.get('measurement_unit')
            if not name or not unit:
                self.stdout.write(
                    self.style.WARNING(
                        f'Пропущен некорректный элемент: {ingredient_item}'
                    )
                )
                skipped += 1
                continue
            ingredients_to_create.append(
                Ingredient(name=name, measurement_unit=unit)
            )

        created_count = Ingredient.objects.bulk_create(
            ingredients_to_create,
            ignore_conflicts=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено ингредиентов: {len(created_count)} '
                f'(всего в файле: {total_count}, '
                f'пропущено некорректных: {skipped})'
            )
        )

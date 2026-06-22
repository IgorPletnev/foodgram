from django.core.management.base import BaseCommand
from recipes.models import Tag


TAGS = [
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
]


class Command(BaseCommand):
    help = 'Создаёт теги по умолчанию, если их нет'

    def handle(self, *args, **options):
        if Tag.objects.exists():
            self.stdout.write('Tags already exist')
            return

        for tag_data in TAGS:
            Tag(**tag_data).save()
            self.stdout.write(f'Tag created: {tag_data["name"]}')

        self.stdout.write(self.style.SUCCESS(f'{len(TAGS)} tags created'))

from rest_framework import serializers


class AbsoluteUrlImageField(serializers.ImageField):
    """Поле для сериализации изображения с абсолютным URL.

    Если request доступен, строит полный URL через build_absolute_uri.
    Если request недоступен — возвращает относительный путь.
    """

    def to_representation(self, image):
        if not image:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(image.url)
        return image.url
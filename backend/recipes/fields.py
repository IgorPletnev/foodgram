from rest_framework import serializers


class AbsoluteUrlImageField(serializers.ImageField):

    def to_representation(self, image):
        if not image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(image.url)
        return image.url
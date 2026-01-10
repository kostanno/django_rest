from rest_framework import serializers
from urllib.parse import urlparse


def validate_youtube_only(value):
    if not value:
        return value

    try:
        parsed_url = urlparse(value)
        domain = parsed_url.netloc.lower()
        if not ('youtube.com' in domain or 'youtu' in domain):
            raise serializers.ValidationError(
                "Разрешены только ссылки на YouTube"
            )

        return value
    except Exception as e:
        raise serializers.ValidationError(f"Ошибка при проверке ссылки: {str(e)}")


class YouTubeURLValidator:

    def __init__(self, field='video_link'):
        self.field = field

    def __call__(self, attrs):
        value = attrs.get(self.field)
        if not value:
            return

        parsed_url = urlparse(value)
        domain = parsed_url.netloc.lower()

        if not ('youtube.com' in domain or 'youtu' in domain):
            raise serializers.ValidationError(
                {self.field: "Разрешены только ссылки на YouTube"}
            )

    def set_context(self, serializer_field):
        self.field = serializer_field.field_name
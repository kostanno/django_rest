from rest_framework import serializers
from urllib.parse import urlparse


class YouTubeURLValidator:


    def __init__(self, field='загрузка видео'):
        self.field = field
        self.allowed_domains = ['youtube.com', 'youtu']

    def __call__(self, value):
        if not value:
            return value

        try:
            parsed_url = urlparse(value)
            domain = parsed_url.netloc.lower()
            is_valid = any(allowed_domain in domain for allowed_domain in self.allowed_domains)

            if not is_valid:
                raise serializers.ValidationError(
                    f"Разрешены только ссылки на YouTube "
                    f"Получена ссылка {value}"
                )

            return value
        except Exception as e:
            raise serializers.ValidationError(
                f"Ошибка при проверке ссылки: {str(e)}"
            )

    def set_context(self, serializer_field):
        pass


class CourseLessonsValidator:

    def __init__(self, field='урок'):
        self.field = field
        self.youtube_validator = YouTubeURLValidator()

    def __call__(self, value):
        if not value:
            return value

        errors = []
        for lesson in value:
            if hasattr(lesson, 'видео загружено') and lesson.video_link:
                try:
                    self.youtube_validator(lesson.video_link)
                except serializers.ValidationError as e:
                    errors.append(f"Урок '{lesson.title}': {e.detail}")
        return value


def validate_youtube_only(value):
    validator = YouTubeURLValidator()
    return validator(value)
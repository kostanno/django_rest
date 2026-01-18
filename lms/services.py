import stripe
import logging
from django.conf import settings
from django.core.exceptions import ValidationError


stripe.api_key = settings.STRIPE_API_KEY
logger = logging.getLogger(__name__)


class StripeService:
    """Сервис для работы с Stripe API."""

    @staticmethod
    def create_product(course):
        """
        Создание продукта в Stripe.
        Документация: https://stripe.com/docs/api/products/create

        Args:
            course (Course): Объект курса

        Returns:
            stripe.Product: Созданный продукт

        Raises:
            ValidationError: Ошибка при создании продукта
        """
        try:
            product_data = {
                'name': course.title,
                'description': course.description[:500] if course.description else None,
                'metadata': {
                    'course_id': str(course.id),
                    'course_owner': str(course.owner.id) if course.owner else '',
                    'type': 'course'
                }
            }

            # Если у курса уже есть Stripe ID, обновляем продукт
            if course.stripe_product_id:
                try:
                    product = stripe.Product.modify(
                        course.stripe_product_id,
                        **product_data
                    )
                    logger.info(f"Product updated: {product.id}")
                    return product
                except stripe.error.InvalidRequestError:
                    # Если продукт не найден, создаем новый
                    pass

            # Создаем новый продукт
            product = stripe.Product.create(**product_data)
            logger.info(f"Product created: {product.id}")
            return product

        except stripe.error.StripeError as e:
            logger.error(f"Stripe product creation error: {str(e)}")
            raise ValidationError(f'Ошибка создания продукта в Stripe: {str(e)}')

    @staticmethod
    def create_price(product_id, amount, currency=settings.DEFAULT_CURRENCY):
        """
        Создание цены в Stripe.
        Документация: https://stripe.com/docs/api/prices/create

        Args:
            product_id (str): ID продукта в Stripe
            amount (Decimal): Сумма в основной валюте
            currency (str): Валюта (по умолчанию 'usd')

        Returns:
            stripe.Price: Созданная цена

        Raises:
            ValidationError: Ошибка при создании цены
        """
        try:
            # Конвертируем сумму в минимальные единицы (центы для USD)
            # Важно: Stripe ожидает сумму в центах/копейках
            unit_amount = int(float(amount) * 100)

            price_data = {
                'product': product_id,
                'unit_amount': unit_amount,
                'currency': currency.lower(),
                'metadata': {
                    'type': 'course_price'
                }
            }

            price = stripe.Price.create(**price_data)
            logger.info(f"Price created: {price.id} - {unit_amount} {currency}")
            return price

        except stripe.error.StripeError as e:
            logger.error(f"Stripe price creation error: {str(e)}")
            raise ValidationError(f'Ошибка создания цены в Stripe: {str(e)}')

    @staticmethod
    def create_checkout_session(price_id, course, user, success_url=None, cancel_url=None):
        """
        Создание сессии оплаты в Stripe.
        Документация: https://stripe.com/docs/api/checkout/sessions/create

        Args:
            price_id (str): ID цены в Stripe
            course (Course): Объект курса
            user (User): Объект пользователя
            success_url (str): URL для перенаправления после успешной оплаты
            cancel_url (str): URL для перенаправления при отмене

        Returns:
            stripe.checkout.Session: Созданная сессия

        Raises:
            ValidationError: Ошибка при создании сессии
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url or settings.PAYMENT_SUCCESS_URL,
                cancel_url=cancel_url or settings.PAYMENT_CANCEL_URL,
                client_reference_id=f'course_{course.id}_user_{user.id}',
                customer_email=user.email,
                metadata={
                    'course_id': str(course.id),
                    'course_title': course.title,
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'payment_type': 'course_purchase'
                },
                shipping_address_collection={
                    'allowed_countries': ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'JP']
                },
                allow_promotion_codes=True,
                billing_address_collection='required',
                locale='auto',
            )

            logger.info(f"Checkout session created: {session.id}")
            return session

        except stripe.error.StripeError as e:
            logger.error(f"Stripe session creation error: {str(e)}")
            raise ValidationError(f'Ошибка создания сессии оплаты: {str(e)}')

    @staticmethod
    def retrieve_session(session_id):
        """
        Получение информации о сессии.
        Документация: https://stripe.com/docs/api/checkout/sessions/retrieve

        Args:
            session_id (str): ID сессии в Stripe

        Returns:
            stripe.checkout.Session: Информация о сессии

        Raises:
            ValidationError: Ошибка при получении сессии
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Stripe session retrieval error: {str(e)}")
            raise ValidationError(f'Ошибка получения информации о сессии: {str(e)}')

    @staticmethod
    def get_test_cards():
        """
        Возвращает список тестовых карт для Stripe.
        Документация: https://stripe.com/docs/terminal/references/testing#standard-test-cards

        Returns:
            dict: Словарь с тестовыми картами
        """
        return {
            'success_cards': [
                {
                    'number': '4242424242424242',
                    'brand': 'Visa',
                    'cvc': '123',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'Стандартная успешная карта'
                },
                {
                    'number': '5555555555554444',
                    'brand': 'Mastercard',
                    'cvc': '123',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'Mastercard успешная'
                },
                {
                    'number': '378282246310005',
                    'brand': 'American Express',
                    'cvc': '1234',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'American Express успешная'
                }
            ],
            'declined_cards': [
                {
                    'number': '4000000000000002',
                    'brand': 'Visa',
                    'cvc': '123',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'Карта отклонена'
                },
                {
                    'number': '4000000000009995',
                    'brand': 'Visa',
                    'cvc': '123',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'Недостаточно средств'
                }
            ],
            'special_cards': [
                {
                    'number': '4000002500003155',
                    'brand': 'Visa',
                    'cvc': '123',
                    'exp_month': '12',
                    'exp_year': '2025',
                    'description': 'Требуется аутентификация 3D Secure'
                }
            ]
        }


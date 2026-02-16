from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from .models import FeedbackMessage, FeedbackSettings
from .serializers import (
    FeedbackCreateSerializer,
    FeedbackResponseSerializer,
    FeedbackListSerializer
)


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet для обратной связи.
    
    POST /api/feedback/ - отправить форму (доступно всем)
    GET /api/feedback/ - список обращений (только админ)
    GET /api/feedback/{id}/ - детали обращения (только админ)
    PATCH /api/feedback/{id}/ - обновить статус (только админ)
    POST /api/feedback/{id}/answer/ - ответить на обращение (только админ)
    """
    
    queryset = FeedbackMessage.objects.all()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        elif self.action in ['list', 'retrieve']:
            return FeedbackListSerializer
        return FeedbackListSerializer

    def create(self, request, *args, **kwargs):
        """
        POST /api/feedback/
        
        Создание обращения из формы обратной связи.
        Доступно без авторизации.
        
        Request:
        {
            "name": "Иван Иванов",
            "email": "ivan@example.com",
            "phone": "+79991234567",
            "message_type": "general",
            "subject": "Вопрос о доставке",
            "message": "Как долго идет доставка в Москву?",
            "attachment": <file>,
            "privacy_policy_accepted": true,
            "privacy_policy_url": "https://site.com/privacy/"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Сохраняем URL политики из настроек, если не передан
        privacy_url = request.data.get('privacy_policy_url', '')
        if not privacy_url:
            # Получаем из настроек site_settings
            from site_settings.models import SiteSetting
            try:
                setting = SiteSetting.objects.get(key='privacy_policy_url')
                privacy_url = setting.get_value() or ''
            except SiteSetting.DoesNotExist:
                privacy_url = ''
        
        # Создаем обращение
        feedback = serializer.save(privacy_policy_url=privacy_url)
        
        # Отправляем email уведомления
        email_sent = self._send_notifications(feedback)
        
        return Response({
            'success': True,
            'message': 'Ваше сообщение успешно отправлено!',
            'feedback_id': feedback.id,
            'email_sent': email_sent
        }, status=status.HTTP_201_CREATED)

    def _send_notifications(self, feedback):
        """Отправка уведомлений о новом обращении"""
        try:
            # Получаем настройки
            try:
                fb_settings = FeedbackSettings.objects.first()
                recipients = fb_settings.get_email_list() if fb_settings else [settings.DEFAULT_FROM_EMAIL]
            except:
                recipients = [settings.DEFAULT_FROM_EMAIL]
            
            # Формируем письмо
            subject = f'Новое обращение #{feedback.id} - {feedback.get_message_type_display()}'
            
            # Текстовое сообщение
            message = f"""
Новое обращение с сайта

ID: {feedback.id}
Тип: {feedback.get_message_type_display()}
Имя: {feedback.name}
Email: {feedback.email}
Телефон: {feedback.phone or 'Не указан'}
Тема: {feedback.subject or 'Без темы'}

Сообщение:
{feedback.message}

{'Прикреплен файл: ' + feedback.attachment_filename if feedback.has_attachment else 'Без вложений'}

Политика конфиденциальности: {'Принята' if feedback.privacy_policy_accepted else 'Не принята'}
URL политики: {feedback.privacy_policy_url or 'Не указан'}

IP: {feedback.ip_address or 'Не определен'}
Страница: {feedback.referer or 'Не определена'}
Время: {feedback.created_at.strftime('%d.%m.%Y %H:%M:%S')}
"""
            
            # HTML версия
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; }}
        .content {{ background: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .field {{ margin-bottom: 15px; }}
        .label {{ font-weight: bold; color: #666; }}
        .message {{ background: white; padding: 15px; border-left: 4px solid #4CAF50; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Новое обращение #{feedback.id}</h2>
            <p>{feedback.get_message_type_display()}</p>
        </div>
        
        <div class="content">
            <div class="field">
                <span class="label">Имя:</span> {feedback.name}
            </div>
            <div class="field">
                <span class="label">Email:</span> <a href="mailto:{feedback.email}">{feedback.email}</a>
            </div>
            <div class="field">
                <span class="label">Телефон:</span> {feedback.phone or 'Не указан'}
            </div>
            <div class="field">
                <span class="label">Тема:</span> {feedback.subject or 'Без темы'}
            </div>
            
            <div class="message">
                <div class="label">Сообщение:</div>
                <p>{feedback.message.replace(chr(10), '<br>')}</p>
            </div>
            
            {'<div class="field"><span class="label">Вложение:</span> ' + feedback.attachment_filename + '</div>' if feedback.has_attachment else ''}
        </div>
        
        <p style="color: #666; font-size: 12px;">
            IP: {feedback.ip_address or 'Не определен'} | 
            Время: {feedback.created_at.strftime('%d.%m.%Y %H:%M:%S')}
        </p>
    </div>
</body>
</html>
"""
            
            # Создаем email
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
                reply_to=[feedback.email]
            )
            email.content_subtype = 'html'
            email.body = html_message
            
            # Прикрепляем файл если есть
            if feedback.has_attachment:
                feedback.attachment.open()
                email.attach(
                    feedback.attachment_filename,
                    feedback.attachment.read(),
                    feedback.attachment.file.content_type
                )
                feedback.attachment.close()
            
            email.send()
            
            # Отправляем подтверждение пользователю
            self._send_confirmation_to_user(feedback)
            
            feedback.email_sent = True
            feedback.save(update_fields=['email_sent'])
            
            return True
            
        except Exception as e:
            feedback.email_error = str(e)
            feedback.save(update_fields=['email_error'])
            print(f"Email sending error: {e}")
            return False

    def _send_confirmation_to_user(self, feedback):
        """Отправка подтверждения пользователю"""
        try:
            subject = 'Ваше обращение принято'
            message = f"""
Здравствуйте, {feedback.name}!

Мы получили ваше обращение №{feedback.id}.
Тема: {feedback.subject or 'Без темы'}

В ближайшее время мы рассмотрим ваш запрос и свяжемся с вами.

С уважением,
Команда поддержки
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[feedback.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Confirmation email error: {e}")

    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """
        POST /api/feedback/{id}/answer/
        
        Ответить на обращение (только админ).
        
        Request:
        {
            "answer_text": "Текст ответа",
            "change_status": true
        }
        """
        feedback = self.get_object()
        
        answer_text = request.data.get('answer_text', '')
        if not answer_text:
            return Response(
                {'error': 'Текст ответа обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Отправляем ответ пользователю
        try:
            subject = f'Ответ на ваше обращение #{feedback.id}'
            message = f"""
Здравствуйте, {feedback.name}!

Вы обращались к нам с вопросом:
{feedback.message}

Наш ответ:
{answer_text}

---
С уважением,
Команда поддержки
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[feedback.email],
                fail_silently=False
            )
            
            # Обновляем статус
            from django.utils import timezone
            feedback.status = 'answered'
            feedback.answered_at = timezone.now()
            feedback.answered_by = request.user
            feedback.save()
            
            return Response({
                'success': True,
                'message': 'Ответ отправлен'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Ошибка отправки: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/feedback/stats/
        
        Статистика обращений (только админ).
        """
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        total = FeedbackMessage.objects.count()
        today = FeedbackMessage.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        this_week = FeedbackMessage.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        by_type = FeedbackMessage.objects.values('message_type').annotate(
            count=Count('id')
        )
        by_status = FeedbackMessage.objects.values('status').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'today': today,
            'this_week': this_week,
            'by_type': {item['message_type']: item['count'] for item in by_type},
            'by_status': {item['status']: item['count'] for item in by_status},
        })


class FeedbackConfigView(generics.GenericAPIView):
    """
    GET /api/feedback/config/
    
    Получение конфигурации формы обратной связи.
    Возвращает URL политики конфиденциальности из настроек.
    Доступно без авторизации.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Получаем настройки
        from site_settings.models import SiteSetting
        
        privacy_url = ''
        try:
            setting = SiteSetting.objects.get(key='privacy_policy_url')
            privacy_url = setting.get_value() or ''
        except SiteSetting.DoesNotExist:
            pass
        
        # Типы обращений
        message_types = [
            {'value': 'general', 'label': 'Общий вопрос'},
            {'value': 'support', 'label': 'Техподдержка'},
            {'value': 'sales', 'label': 'Отдел продаж'},
            {'value': 'partnership', 'label': 'Партнерство'},
            {'value': 'complaint', 'label': 'Жалоба'},
            {'value': 'other', 'label': 'Другое'},
        ]
        
        return Response({
            'privacy_policy_url': privacy_url,
            'privacy_policy_required': True,
            'max_file_size': 10 * 1024 * 1024,  # 10MB в байтах
            'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif', 'pdf'],
            'allowed_content_types': [
                'image/jpeg',
                'image/png',
                'image/gif',
                'application/pdf'
            ],
            'message_types': message_types,
        })
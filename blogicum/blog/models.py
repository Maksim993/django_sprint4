from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True

    #def __str__(self):
    #   return self.title


class Post(BaseModel):
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    # ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ИЗОБРАЖЕНИЯ
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True,
        null=True,
        help_text='Загрузите изображение для публикации'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    # ДОБАВЛЯЕМ __str__ для Post
    def __str__(self):
        return self.title


class Category(BaseModel):
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    # ДОБАВЛЯЕМ __str__ для Post
    def __str__(self):
        return self.title


class Location(BaseModel):
    name = models.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    # ДОБАВЛЯЕМ __str__ для Location
    def __str__(self):
        return self.name
    

class Comment(models.Model):
    """Модель комментария к посту"""
    text = models.TextField('Текст комментария')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']  # Сортировка от старых к новым

    def __str__(self):
        return f'Комментарий от {self.author} к {self.post}'

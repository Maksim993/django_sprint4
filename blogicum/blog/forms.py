from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from .models import Post, Category, Location, Comment

User = get_user_model()


class UserUpdateForm(UserChangeForm):
    """Форма для обновления данных пользователя"""
    
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов"""
    
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем только опубликованные категории и локации
        self.fields['category'].queryset = Category.objects.filter(is_published=True)
        self.fields['location'].queryset = Location.objects.filter(is_published=True)
        
        # Добавляем обязательность полей
        self.fields['category'].required = True
        self.fields['title'].required = True
        self.fields['text'].required = True
        self.fields['pub_date'].required = True


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишите комментарий...'}),
        }
        labels = {
            'text': '',
        }
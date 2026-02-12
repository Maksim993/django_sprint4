from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Category, Comment
from django.contrib.auth import get_user_model
from django.views.generic import DetailView, UpdateView, ListView, CreateView, DeleteView
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .forms import UserUpdateForm, PostForm, CommentForm
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden
from django.db import models
from django.contrib.auth.decorators import login_required



User = get_user_model()


class IndexListView(ListView):
    """Главная страница со списком постов"""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    context_object_name = 'posts'
    
    def get_queryset(self):
        """Фильтруем только опубликованные посты с актуальной датой"""
        return Post.objects.select_related('category').annotate(
            comment_count=models.Count('comments')
        ).filter(
            category__is_published=True,
            is_published=True,
            pub_date__lte=timezone.now()  # Только посты с прошедшей датой
        ).order_by('-pub_date')


class PostDetailView(DetailView):
    """Страница отдельного поста"""
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'id'
    
    def get_queryset(self):
        """Фильтруем посты для разных пользователей"""
        user = self.request.user
        
        # Получаем базовый queryset
        queryset = Post.objects.select_related('category')
        
        # Если пользователь авторизован
        if user.is_authenticated:
            # Проверяем каждый пост отдельно
            allowed_posts = []
            for post in queryset:
                # Если пользователь автор ИЛИ пост опубликован с прошедшей датой
                if post.author == user or (
                    post.category.is_published and 
                    post.is_published and 
                    post.pub_date <= timezone.now()
                ):
                    allowed_posts.append(post.id)
            
            # Возвращаем только разрешенные посты
            return queryset.filter(id__in=allowed_posts)
        
        # Для неавторизованных - только опубликованные с прошедшей датой
        return queryset.filter(
            category__is_published=True,
            is_published=True,
            pub_date__lte=timezone.now()
        )
    
    def get_context_data(self, **kwargs):
        """Добавляем форму комментария и список комментариев"""
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Форма для нового комментария
        context['form'] = CommentForm()
        
        # Комментарии к посту (уже отсортированы в модели Meta.ordering)
        context['comments'] = post.comments.select_related('author').all()
        
        return context


class CategoryPostsListView(ListView):
    """Страница категории со списком постов"""
    template_name = 'blog/category.html'
    paginate_by = 10
    context_object_name = 'posts'
    
    def get_queryset(self):
        """Получаем посты для указанной категории"""
        category_slug = self.kwargs.get('category_slug')
        self.category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        
        return Post.objects.select_related('category').annotate(
            comment_count=models.Count('comments')
        ).filter(
            category=self.category,
            is_published=True,
            pub_date__lte=timezone.now()  # Только посты с прошедшей датой
        ).order_by('-pub_date')
    
    def get_context_data(self, **kwargs):
        """Добавляем категорию в контекст"""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class UserProfileView(DetailView):
    """Страница профиля пользователя"""
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        """Получаем пользователя по username из URL"""
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)
    
    def get_context_data(self, **kwargs):
        """Добавляем посты пользователя в контекст с пагинацией"""
        context = super().get_context_data(**kwargs)
        
        # Получаем пользователя
        user = self.object
        
        # Получаем посты пользователя
        if self.request.user == user:
            # Автор видит ВСЕ свои посты (включая отложенные и неопубликованные)
            posts = Post.objects.filter(author=user)
        else:
            # Остальные видят только опубликованные посты с актуальной датой
            posts = Post.objects.filter(
                author=user,
                is_published=True,
                pub_date__lte=timezone.now()
            )
        # Добавляем аннотацию с количеством комментариев
        posts = posts.annotate(comment_count=models.Count('comments'))

        # Сортируем по дате публикации (новые сверху)
        posts = posts.order_by('-pub_date')
        
        # Пагинация через Paginator
        from django.core.paginator import Paginator
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['page_obj'] = page_obj
        return context
    

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Страница редактирования профиля"""
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'  # Используем ваш шаблон
    success_url = reverse_lazy('blog:profile')  # Будем переопределять
    
    def get_object(self):
        """Получаем текущего пользователя"""
        return self.request.user
    
    def get_success_url(self):
        """Перенаправляем на страницу профиля после успешного обновления"""
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})
    
    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        # В шаблоне уже есть {{ request.user.username }}, но можно добавить
        return context
    

class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста"""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    
    def form_valid(self, form):
        """Привязываем автора к посту перед сохранением"""
        form.instance.author = self.request.user
        # Автоматически публикуем пост (is_published=True по умолчанию в BaseModel)
        response = super().form_valid(form)
        return response
    
    def get_success_url(self):
        """После создания перенаправляем на страницу профиля автора"""
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})
    

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование существующего поста"""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    context_object_name = 'post'
    pk_url_kwarg = 'id'  # Указываем, что параметр в URL называется 'id'
    
    def test_func(self):
        """Проверка, что текущий пользователь - автор поста"""
        post = self.get_object()
        return self.request.user == post.author
    
    def handle_no_permission(self):
        """Что делать, если у пользователя нет прав на редактирование"""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            post = self.get_object()
            return redirect('blog:post_detail', id=post.id)
    
    def get_success_url(self):
        """После редактирования перенаправляем на страницу поста"""
        return reverse('blog:post_detail', kwargs={'id': self.object.id})
    

    # ДЛЯ ДОБАВЛЕНИЯ КОММЕНТАРИЯ (FBV - проще для обработки POST)
@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту"""
    post = get_object_or_404(Post, pk=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
            return redirect('blog:post_detail', id=post.id)
    else:
        form = CommentForm()
    
    # Если GET запрос - перенаправляем на страницу поста
    return redirect('blog:post_detail', id=post.id)


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование комментария"""
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'  # Используем готовый шаблон
    pk_url_kwarg = 'comment_id'
    
    def test_func(self):
        """Проверка, что текущий пользователь - автор комментария"""
        comment = self.get_object()
        return self.request.user == comment.author
    
    def handle_no_permission(self):
        """Что делать, если у пользователя нет прав"""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            comment = self.get_object()
            messages.error(self.request, 'Вы можете редактировать только свои комментарии')
            return redirect('blog:post_detail', id=comment.post.id)
    
    def get_success_url(self):
        """После редактирования перенаправляем на страницу поста"""
        return reverse('blog:post_detail', kwargs={'id': self.object.post.id})
    
    def form_valid(self, form):
        """При успешном редактировании комментария"""
        response = super().form_valid(form)
        messages.success(self.request, 'Комментарий обновлен!')
        return response
    
    def get_context_data(self, **kwargs):
        """Передаем комментарий в контекст"""
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context
    

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление публикации"""
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'id'
    form_class = PostForm

    def get_queryset(self):
        return super().get_queryset().select_related('location', 'category', 'author')
    
    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if request.user != post.author:
            return redirect('blog:post_detail', id=post.id)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})
    

class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария"""
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    
    def dispatch(self, request, *args, **kwargs):
        """Проверяем, что пользователь - автор комментария"""
        comment = self.get_object()
        if request.user != comment.author:
            return redirect('blog:post_detail', id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """После удаления на страницу поста"""
        comment = self.get_object()
        return reverse('blog:post_detail', kwargs={'id': comment.post.id})
from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    """Страница О проекте"""
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """Страница Правила"""
    template_name = 'pages/rules.html'


# Обработчики ошибок
def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request):
    return render(request, 'pages/500.html', status=500)
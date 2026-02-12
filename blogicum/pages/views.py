from django.views.generic import TemplateView


class AboutView(TemplateView):
    """Страница О проекте"""
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """Страница Правила"""
    template_name = 'pages/rules.html'
    
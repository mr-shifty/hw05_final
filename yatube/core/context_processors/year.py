import datetime


def year(request):
    """Добавляет в контекст переменную greeting с приветствием."""""
    return {
        'year': datetime.datetime.today().year
    }

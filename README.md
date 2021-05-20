# prpr

![example workflow](https://github.com/salmiakki/prpr/actions/workflows/actions.yaml/badge.svg)


Вряд ли вы здесь случайно.

## Как воспользоваться

Нужен Python 3.9+.

### Dotfile

В `~/.prpr.yaml` нужно положить токен доступа к Стартреку:

```yaml
startrek_token: your_token_here
```

### Запуск

Клонируем, (по желанию) создаем окружение, ставим зависимости.

```bash
python3 -m prpr.main
```

Также удобно создать bash alias, 
чтобы можно было запускать из любого местоположения, например, так:
```
alias prpr='cd /path/to/dir/prpr/ && source venv/bin/activate && python -m prpr.main'
```

### Опции запуска

```
usage: main.py [-h] [-m {default,all,open,closed}] [-p PROBLEMS [PROBLEMS ...]] [-n NO] [-s STUDENT] [-o] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -o, --open            Open homework pages in browser
  -v, --verbose

filters:
  these allow to specify the subset of homeworks to be displayed, can be composed

  -m {default,all,open,closed}, --mode {default,all,open,closed}
                        filter by status mode
                                default: in review, open or on the side of user
                                open: in review or open
                                closed: resolved or closed
                                all: all, duh
  -p PROBLEMS [PROBLEMS ...], --problems PROBLEMS [PROBLEMS ...]
                        the numbers of problems to be shown; multiple space-separated values are accepted
  -n NO, --no NO        the no of the homework to be shown, all other filters are ignored
  -s STUDENT, --student STUDENT
                        the substring to be found in the student column, mail works best
```

### Примеры использования опций запуска

Вывести только 1 и 2 проекты:

```bash
python -m prpr.main --problems 1 2
```

Открыть в браузере работу № 100:

```bash
python -m prpr.main --no 100 --open
```

Вывести все работы по конкретному студенту (емейл, имя, фамилия). 
Фильтр работает только по одному слову (до первого пробела):

```bash
python -m prpr.main --mode all --student ivanov@yatube.ru
```


## Тубидубидутуду

1. Заполнить этот документ
1. Показывать номер итерации
1. Настройки и украшения
1. Создать пакет cо скриптом запуска
1. Уведомления
1. Скачивание
1. Запуск сторонних инструментов (линтеры итп)
1. Дифф
1. Статистика
1. Тесты 😹
1. Поддержать несколько разных курсов
1. Кэширование
1. Демонстрационный запуск

# samson_test_task_blender

Задание с реализацией воссоздания сцены из json-файла в 3d модель

>[!WARNING]
>подрузамеввается что все действия будут воспроизводиться из корня папки

* [Техническое Задание](./dock/myTZ.md)

## Клонирование

```cmd
git clone https://github.com/nais2008/samson_test_task_blender
cd ./samson_test_task_blender/
```

## Установка виртуального окружения

```cmd
python3 -m venv venv
source ./venv/Scripts/activate
```

## Установка зависимостей

### Для выпуска

```cmd
pip3 install -r ./requirements/prod.txt
```

### Для разработки

```cmd
pip3 install -r ./requirements/dev.txt
```

### Для тестирования

```cmd
pip3 install -r ./requirements/test.txt
```

## Заполняем переменные окружения

### Создаем файл

```cmd
touch .env
```

### Заполняем

```env
# Секретный ключ, должен быть индивидуален и засекерчен
DJANGO_SECRET_KEY=your_secret_key
# Включение DEBUG для приложения
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

## Запуск проекта

```cmd
cd ./samson/
python3 manage.py runserver
```

## Запуск миграций в базе данных

```cmd
cd ./samson/
python3 manage.py migrate
```

## Я старался, рад буду если прочитали)

![enot](dock/img.jpg)

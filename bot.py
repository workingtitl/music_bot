import telebot
import re
from yandex_music import Client
from decouple import config

# Ваш токен Telegram бота
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN') 

# Ваш OAuth токен Яндекс Музыки
YANDEX_MUSIC_TOKEN = config('YANDEX_MUSIC_TOKEN')

# Ваш uuid плейлиста
playlist_uuid = config('playlist_uuid')

# Ссылка для сообщения
link = config('link')

# Имя плейлиста
playlist_name = config('playlist_name')

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализация клиента Яндекс Музыки
client = Client(YANDEX_MUSIC_TOKEN).init()

@bot.message_handler(commands=['start'])
def send_welcome(message): bot.reply_to(message,f"Просто отправляй мне ссылки на треки в Яндекс Музыке, и я добавлю их в плейлист - {link}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Извлечение идентификаторов альбома и трека из ссылки
        album_id, track_id = extract_album_and_track_id(message.text)
        if album_id == None:
            # Получите информацию о треке
            track_info = client.tracks(track_id)[0]
            # Извлеките album_id из информации о треке
            album_id = track_info.albums[0].id
        
        # Извлечение номера ревизии плейлиста
        playlists = client.users_playlists_list()
        # Переменная для хранения значения revision
        r = None
        # Проход по списку плейлистов и поиск плейлиста с нужным названием
        for playlist in playlists:
            if playlist['title'] == playlist_name:
                r = playlist['revision']
                break

        # Добавление трека в плейлист с учетом ревизии
        client.users_playlists_insert_track(playlist_uuid, track_id, album_id, revision=r)
        bot.reply_to(message, "Трек успешно добавлен в плейлист!")
 
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

def extract_album_and_track_id(url):
    # Регулярное выражение для извлечения идентификаторов альбома и трека
    track_pattern = re.compile(r'https://music\.yandex\.ru/track/(\d+)')
    album_track_pattern = re.compile(r'https://music\.yandex\.ru/album/(\d+)/track/(\d+)')

    track_match = track_pattern.match(url)
    album_track_match = album_track_pattern.match(url)

    if track_match:
        return None, track_match.group(1)
    elif album_track_match:
        return album_track_match.group(1), album_track_match.group(2)
    else:
        raise ValueError("Неверная ссылка на трек")

# Запуск бота
bot.polling()

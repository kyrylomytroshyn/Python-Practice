from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, Error
import json
import sqlite3


def create_connection(db_file):
    """ Инициализация соединения с базой sqlite3 """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        return conn


handle = open("Key.txt", "r")
# Youtube API Key, который хранится в файле
api_key = handle.readline()
handle.close()

youtube = build('youtube', 'v3', developerKey=api_key)


def server_request(request: json):
    """
    Функция обработки результата запроса.
    Если ошибок нет - возвращает json ответ сервера, иначе Exception.
    """

    try:
        response = request.execute()
        print(json.dumps(response, indent=1))  # Для улучшения читаемости json
        return json.dumps(response, indent=1)
    except HttpError as e:
        print('Error response status code : {0}, reason : {1}'.format(e.status_code, e.error_details))


def add_search(conn: sqlite3, request: str, search_text: str):
    """
    Проверяет наличие записи в таблице.
    Возвращает данные, если запись имеется, иначе None.
    """

    sql = '''INSERT INTO search (text, result) VALUES (?,?)'''

    cur = conn.cursor()
    cur.execute(sql, (search_text, request))
    conn.commit()


def check_search(conn: sqlite3, search_text: str):
    """
    Проверяет наличие записи в таблице.
    Возвращает данные, если запись имеется, иначе None.
    """
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM search WHERE text like '{search_text}'")

    rows = cur.fetchall()

    if rows is not None:
        for row in rows:
            return row
    else:
        return None


def searching_video(conn: sqlite3, searching_text: str):
    """
    Функция поиска видео, входные параметры:
     - searching_text - текст поиска
    Возвращает json результат запроса или к базе данных или к API (в зависимости от того найдет или нет).
    """
    searching_result = check_search(conn, searching_text)
    if searching_result is None:
        request = youtube.search().list(
            part='snippet',
            maxResults=25,
            q=searching_text
        )
        tmp = server_request(request)
        add_search(conn, tmp, searching_text)
        return tmp
    else:
        return searching_result


def update_like(conn, video_info: str, like: int):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM liked WHERE video_info like '{video_info}'")

    rows = cur.fetchall()

    try:
        if rows is None:
            cur.execute('INSERT INTO liked (video_info, like) VALUES (?,?)', (video_info, like))
            conn.commit()
        else:
            cur.execute("UPDATE liked SET 'like' = ? WHERE video_info LIKE (?)", (like, video_info))
            conn.commit()
        return True
    except Error as e:
        print(e)
        return False


def like_video(conn: sqlite3, video_info: str):
    """
    Функция добавления видео в понравившеися, входные параметры:
     - video_info - текст поиска.
    """
    return update_like(conn, video_info, 1)


def dislike_video(conn: sqlite3, video_info: str):
    """
    Функция добавления видео в непонравившеися, входные параметры:
     - video_info - текст поиска.
    """
    return update_like(conn, video_info, 0)


def get_video_likes(conn: sqlite3):
    """
    Функция получения понравившеиехся видео, входные параметры:
     - video_id - текст поиска.
    """
    cur = conn.cursor()
    cur.execute('SELECT video_info FROM liked WHERE like = 1')
    conn.commit()
    rows = cur.fetchall()
    print(rows)


def main():
    """Все функции  с получением данных вызываются по очереди с подготовленными данными
    Для проверки реализации связи с базой данных и API. Так как Front-End отсутствует, вывожу всё в консоль"""

    connect = create_connection(r"C:\Users\Kyrylo\Documents\youtube_database.db")
    print(searching_video(connect, 'Lo-Fi Hip-Ho'))  # Выведет json со всеми данными с YouTube
    print(dislike_video(connect,
                        """  {
   "kind": "youtube#searchResult",
   "etag": "asKVqprCkrtBPVsXpeCCkwxCLIk",
   "id": {
    "kind": "youtube#video",
    "videoId": "vEX7nUP2IuA"
   },
   "snippet": {
    "publishedAt": "2021-05-26T00:58:22Z",
    "channelId": "UCyD59CI7beJDU493glZpxgA",
    "title": "4K Space Lofi Radio 24/7 Aesthetic Lofi Hip Hop Beats to Chill / Study to",
    "description": "Welcome to the year 2069, where space travelling is cheap and safe. This is your room in the Space Hotel, here you can spend the night and chill with lofi beats ...",
    "thumbnails": {
     "default": {
      "url": "https://i.ytimg.com/vi/vEX7nUP2IuA/default_live.jpg",
      "width": 120,
      "height": 90
     },
     "medium": {
      "url": "https://i.ytimg.com/vi/vEX7nUP2IuA/mqdefault_live.jpg",
      "width": 320,
      "height": 180
     },
     "high": {
      "url": "https://i.ytimg.com/vi/vEX7nUP2IuA/hqdefault_live.jpg",
      "width": 480,
      "height": 360
     }
    },
    "channelTitle": "lofi geek",
    "liveBroadcastContent": "live",
    "publishTime": "2021-05-26T00:58:22Z"
   }
  },"""))

    print(get_video_likes(connect))


if __name__ == '__main__':
    main()

import json
from flask import Flask, render_template, request, redirect, url_for
from apiclient.discovery import build

app = Flask(__name__)


# --------------------------------------------------------------------------------------
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from apiclient.discovery import build

today = date.today()
youtube_today = datetime.strftime(today, '%Y-%m-%dT%H:%M:%S.%fZ')
three_month_ago = today - relativedelta(months = 3)
youtube_three_month_ago = datetime.strftime(three_month_ago, '%Y-%m-%dT%H:%M:%S.%fZ')

YOUTUBE_API_KEY = 'AIzaSyB9ZZfCINIyBTP0KWMizMhamUOUhpKn8p8'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

youtube = build(
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    developerKey = YOUTUBE_API_KEY
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search.html')
    else:
        form_input = request.form['input']

        channel_id_search_response = youtube.search().list(
            part = 'id, snippet',  # idも指定可能。idとsnippetの両方を対象にする場合は'id,snippet'と指定する。
            q = form_input,  # 検索ワードー複数
            maxResults = 10,  # 最大出力本数
            type = 'channel',  # タイプーvideo, channel, playlist　複数指定はカンマで区切る
            order = 'relevance',  # 並べ替えーrelevance:関連度順, date:アップロード日, videoCount:視聴回数, rating:評価, title：？
        ).execute()

        # 何を出力する？一旦タイトルとチャンネル名
        channel_id_items = channel_id_search_response['items']
        small_list = []
        large_list = []

        for item in range(len(channel_id_items)):
            thumbnail = channel_id_items[item]['snippet']['thumbnails']['default']['url']
            small_list.append(thumbnail)

            channelTitle = channel_id_items[item]['snippet']['title']
            small_list.append(channelTitle)

            overview = channel_id_items[item]['snippet']['description']
            small_list.append(overview)

            channelId = channel_id_items[item]['id']['channelId']
            small_list.append(channelId)
            large_list.append(small_list)
            small_list = []

        return render_template(
            'search.html', 
            len = len, 
            large_list = large_list
        )

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'GET':
        return render_template('result.html')
    else:
        SEARCH_ID = request.form['channel_id']

        # チャンネル情報
        def youtube_channel_detail(channel_id, api_key):
            response = youtube.channels().list(
                part = 'id, snippet, statistics',
                id = channel_id
            ).execute()

            return response['items'][0]

        d = youtube_channel_detail(SEARCH_ID, YOUTUBE_API_KEY)

        # 直近3ヶ月
        three_months_search_response = youtube.search().list(
            part = 'id, snippet',
            channelId = SEARCH_ID,
            maxResults = 100,
            publishedAfter = youtube_three_month_ago,
            type = 'video',
            order = 'date',
        ).execute()

        # 直近30本
        thirty_search_response = youtube.search().list(
            part = 'id, snippet',
            channelId = SEARCH_ID,
            maxResults = 30,
            type = 'video',
            order = 'date',
        ).execute()

        def get_video_statistics(id):
            statistics = youtube.videos().list(part = 'statistics', id = id).execute()['items'][0]['statistics']
            return statistics

        # 合計再生回数（直近3ヶ月）を出力
        three_months_items = three_months_search_response['items']
        three_months_view_count = 0

        for item in range(len(three_months_items)):
            videoId = three_months_items[item]['id']['videoId']
            viewCount = get_video_statistics(videoId)['viewCount']
            three_months_view_count += int(viewCount)

        # 合計再生回数（直近30本）, 合計高評価数（直近30本）, 合計低評価数（直近30本）を出力
        thirty_items = thirty_search_response['items']
        thirty_videos_view_count = 0
        thirty_videos_like_count = 0
        thirty_videos_dislike_count = 0

        for item in range(len(thirty_items)):
            videoId = thirty_items[item]['id']['videoId']
            viewCount = get_video_statistics(videoId)['viewCount']
            likeCount = get_video_statistics(videoId)['likeCount']
            dislikeCount = get_video_statistics(videoId)['dislikeCount']

            thirty_videos_view_count += int(viewCount)
            thirty_videos_like_count += int(likeCount)
            thirty_videos_dislike_count += int(dislikeCount)

        # チャンネル名:
        # d['snippet']['title']

        # チャンネル登録者数
        subscribers_count = int(d['statistics']['subscriberCount'])

        # 合計再生回数（直近3ヶ月）
        # three_months_view_count

        # 平均再生回数（直近30本）
        avarage_view_count = int(thirty_videos_view_count / len(thirty_items))

        # 累計再生回数
        total_view_count = int(d['statistics']['viewCount'])

        # YouTube歴
        youtube_published_date = d['snippet']['publishedAt']
        if '.' in youtube_published_date :
            published_date = datetime.strptime(youtube_published_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            career = today - published_date.date()
        else:
            published_date = datetime.strptime(youtube_published_date, '%Y-%m-%dT%H:%M:%S%fZ')
            career = today - published_date.date()

        # 投稿動画本数
        total_video_count = int(d['statistics']['videoCount'])

        # 平均再生回数/登録者数%
        if subscribers_count == 0 or avarage_view_count == 0:
            view_percentage = 0
        else:
            view_percentage = int(avarage_view_count / subscribers_count * 100)

        # 高評価率（直近30本）
        if thirty_videos_like_count == 0:
            like_percentage = 0
        elif thirty_videos_dislike_count == 0:
            like_percentage = 100
        else:            
            like_percentage = int(100 - thirty_videos_dislike_count / thirty_videos_like_count * 100)

        # 評価if文
        subscribers_score = 0
        if subscribers_count >= 3000000:
            subscribers_score = 50
        elif subscribers_count >= 1000000:
            subscribers_score = 40
        elif subscribers_count >= 500000:
            subscribers_score = 30
        elif subscribers_count >= 50000:
            subscribers_score = 20
        elif subscribers_count >= 1000:
            subscribers_score = 10

        three_months_view_count_score = 0
        if three_months_view_count >= 100000000:
            three_months_view_count_score = 5
        elif three_months_view_count >= 50000000:
            three_months_view_count_score = 4
        elif three_months_view_count >= 10000000:
            three_months_view_count_score = 3
        elif three_months_view_count >= 1000000:
            three_months_view_count_score = 2
        elif three_months_view_count >= 10000:
            three_months_view_count_score = 1

        avarage_view_count_score = 0
        if  avarage_view_count >= 1000000:
            avarage_view_count_score = 5
        elif avarage_view_count >= 500000:
            avarage_view_count_score = 4
        elif avarage_view_count >= 100000:
            avarage_view_count_score = 3
        elif avarage_view_count >= 10000:
            avarage_view_count_score = 2
        elif avarage_view_count >= 1000:
            avarage_view_count_score = 1

        total_view_count_score = 0
        if total_view_count >= 1000000000:
            total_view_count_score = 5
        elif total_view_count >= 100000000:
            total_view_count_score = 4
        elif total_view_count >= 50000000:
            total_view_count_score = 3
        elif total_view_count >= 10000000:
            total_view_count_score = 2
        elif total_view_count >= 1000000:
            total_view_count_score = 1

        career_days_score = 0
        if career.days >= 1825:
            career_days_score = 5
        elif career.days >= 1460:
            career_days_score = 4
        elif career.days >= 1095:
            career_days_score = 3
        elif career.days >= 730:
            career_days_score = 2
        elif career.days >= 365:
            career_days_score = 1

        total_video_count_score = 0
        if total_video_count >= 1000:
            total_video_count_score = 5
        elif total_video_count >= 500:
            total_video_count_score = 4
        elif total_video_count >= 250:
            total_video_count_score = 3
        elif total_video_count >= 100:
            total_video_count_score = 2
        elif total_video_count >= 50:
            total_video_count_score = 1

        view_percentage_score = 0
        if view_percentage >= 50:
            view_percentage_score = 5
        elif view_percentage >= 30:
            view_percentage_score = 4
        elif view_percentage >= 10:
            view_percentage_score = 3
        elif view_percentage >= 5:
            view_percentage_score = 2
        elif view_percentage >= 1:
            view_percentage_score = 1

        like_percentage_score = 0
        if like_percentage >= 95:
            like_percentage_score = 5
        elif like_percentage >= 90:
            like_percentage_score = 4
        elif like_percentage >= 80:
            like_percentage_score = 3
        elif like_percentage >= 70:
            like_percentage_score = 2
        elif like_percentage >= 50:
            like_percentage_score = 1

        # 評価
        view_count_score = three_months_view_count_score * 5 + avarage_view_count_score * 5
        career_score = total_view_count_score * 6 + career_days_score * 2 + total_video_count_score * 2
        love_score = view_percentage_score * 5 + like_percentage_score * 5
        total_score = subscribers_score + view_count_score + career_score + love_score

        catch_copy = [
            'え、誰それ？',    
            'これからに期待',
            '知る人ぞ知る',
            'そこそこ人気あるよね',
            'みんなの人気者！',
            '誰もが崇める…'
            ]

        total_rank = [
            'Eランク：ただの一般人', 
            'Dランク：底辺YouTuber', 
            'Cランク：マイナーYouTuber', 
            'Bランク：そこそこのYouTuber', 
            'Aランク：トップYouTuber', 
            'Sランク：神YouTuber'
            ]
        
        if total_score >= 180:
            final_catch_copy = catch_copy[5]
            final_total_rank = total_rank[5]
        elif total_score >= 150:
            final_catch_copy = catch_copy[4]
            final_total_rank = total_rank[4]
        elif total_score >= 100:
            final_catch_copy = catch_copy[3]
            final_total_rank = total_rank[3]
        elif total_score >= 80:
            final_catch_copy = catch_copy[2]
            final_total_rank = total_rank[2]
        elif total_score >= 51:
            final_catch_copy = catch_copy[1]
            final_total_rank = total_rank[1]
        else:
            final_catch_copy = catch_copy[0]
            final_total_rank = total_rank[0]

        subscribers_score = subscribers_score / 10 
        view_count_score = view_count_score / 10 
        career_score = career_score / 10 
        love_score = love_score / 10 

        subscribers_review =[
            'ほとんどいません！もっと頑張りましょう…',
            'まだまだ少ない！でも伸びしろしかない！',
            'クラスに一人知っている人がいるかいないかってところでしょう',
            'なかなかの登録者数！立派な「YouTuber」だと胸を張れるでしょう',
            '100万人以上！トップYouTuberの一員です',
            '国内最高レベルの登録者数がいます！まさに神レベル！'
        ]

        view_count_review = [
            '全然再生されていません！もっと面白い動画いっぱい作って〜',
            'う〜んってところ。まだまだ有名にはなれません！',
            'まあまあな再生回数！でももっと伸ばしていきたいね',
            'これだけあればYouTubeでご飯も食べていけるでしょう',
            'かなりの再生回数！広告収入もきっとすごい！',
            '億万長者だ！まさにYouTubeドリーム！！'
        ]

        career_review = [
            'まだまだ駆け出し！諦めずに続けていってほしい',
            'そろそろ初心者YouTuber卒業？これからに期待！',
            'だんだん自信もついてきた？でも油断は禁物！',
            '中堅といったところでしょうか？しかしトップレベルにはまだ遠い！',
            'なかなかの実績です！トップレベルまであと一歩！',
            '継続は力なり！他YouTuberへの影響力もかなりのもの！？'
        ]

        love_review = [
            '正直視聴者に愛されてない？もっと好感度あげてこ〜',
            '結構好感度低い？もしかしてオワコンの前触れかも…',
            '微妙なラインです…。高評価とかもっと意識して！',
            'そこそこの愛され具合！でも炎上には気をつけて！',
            '結構視聴者に愛されていますね。チャンネル登録者も増えやすい！',
            '視聴者にめちゃくちゃ愛されています！その調子！'
        ]

        if subscribers_score > 4:
            final_subscribers_review = subscribers_review[5]
        elif subscribers_score > 3:
            final_subscribers_review = subscribers_review[4]
        elif subscribers_score > 2:
            final_subscribers_review = subscribers_review[3]
        elif subscribers_score > 1:
            final_subscribers_review = subscribers_review[2]
        elif subscribers_score > 0:
            final_subscribers_review = subscribers_review[1]
        else:
            final_subscribers_review = subscribers_review[0]
        
        if view_count_score > 4:
            final_view_count_review = view_count_review[5]
        elif view_count_score > 3:
            final_view_count_review = view_count_review[4]
        elif view_count_score > 2:
            final_view_count_review = view_count_review[3]
        elif view_count_score > 1:
            final_view_count_review = view_count_review[2]
        elif view_count_score > 0:
            final_view_count_review = view_count_review[1]
        else:
            final_view_count_review = view_count_review[0]

        if career_score > 4:
            final_career_review = career_review[5]
        elif career_score > 3:
            final_career_review = career_review[4]
        elif career_score > 2:
            final_career_review = career_review[3]
        elif career_score > 1:
            final_career_review = career_review[2]
        elif career_score > 0:
            final_career_review = career_review[1]
        else:
            final_career_review = career_review[0]
        
        if love_score > 4:
            final_love_review = love_review[5]
        elif love_score > 3:
            final_love_review = love_review[4]
        elif love_score > 2:
            final_love_review = love_review[3]
        elif love_score > 1:
            final_love_review = love_review[2]
        elif love_score > 0:
            final_love_review = love_review[1]
        else:
            final_love_review = love_review[0]

        return render_template(
            'result.html',
            final_catch_copy = final_catch_copy, 
            final_total_rank = final_total_rank, 
            subscribers_score = subscribers_score, 
            view_count_score = view_count_score, 
            career_score = career_score, 
            love_score = love_score,
            final_subscribers_review = final_subscribers_review,
            final_view_count_review = final_view_count_review,
            final_career_review = final_career_review,
            final_love_review = final_love_review
        )

if __name__ == '__main__':
    app.run(debug = True)
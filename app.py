# abort（400)→リクエストをエラーコードで中断するメソッド
from flask import Flask, request, abort, session

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate, URIAction 
)
import pandas as pd


# =====================================FireBase設定=============================================================-=
# FireStore読み込み
from firebase_admin import firestore
import firebase_admin
from firebase_admin import db
# 認証メソッドをインポート
from firebase_admin import credentials
# apiKeyがあるJsonファイルを取得
cred = credentials.Certificate(
    "find-me-364404-ac6d426ad37d.json")

# 初期化
firebase_admin.initialize_app(cred)

# FireStore_dbと接続
db = firestore.client()

  


# =============================================================================================================
# Lineで登録したBOTのトークンとチャンネルシークレット
line_bot_api = LineBotApi(
    'mFvkEpqmXVupgXOxBRMxbMBYQ8z0XlsP0VBDEMcvIM86Q73F+I+1faFMqzkvkYsQ75LnmacslH/8iIB13z7e3MwGVQR4wR0K3l24irRYGOII3vhlMNCxLjA6JfbOcqOgMHT71hVmxGZVYAaEef83pgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('41fe6d837a5cd1387a9e7f3fc13590e2')

# Flaskでリクエスト、レスポンスを行いますよ〜
app = Flask(__name__)


@app.route("/")
def Test():
    return "OK!!"


# 「こういうラインボットがあるよ～」って知らせる処理
@app.route("/callback", methods=['POST'])
def callback():

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print(body)
    # handle webhook body
    try:
        handler.handle(body, signature)
        print('ok??')
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'
    print(body)


#===========================================dbから'text'を取得してカウント==================================================================================================


def msg_count(text, user_id):
    query = db.collection('users').where('user_id', '==', user_id)
    docs = query.stream()

    d_res = []
    s_res = []
    for doc in docs:
        d = doc.get('timestamp')
        d_res.append(d)
        s = doc.get('text')
        s_res.append(s)

    tmp = pd.DataFrame({'dt':d_res, 'msg':s_res}).sort_values('dt').reset_index(drop=True)
    th = tmp['dt'][0]
    for i, r in tmp.iterrows():
        if r['msg']=='始める':
            th = r['dt']
    tar = tmp.loc[tmp['dt']>=th].copy()
    tar['cnt'] = tar.rank()['dt']-1
    cnt = tar.loc[tar['msg']==text, 'cnt'].values[0]
    return cnt

#===============================================返信処理======================================================================================================

# オウム返ししている記述
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # user_idをprofileに格納
    profile = line_bot_api.get_profile(event.source.user_id)


    #fire storeドキュメントに上書きされないようにする
    data = {
        u'user_id':profile.user_id
        ,u'text':event.message.text
        , u'user_name':profile.display_name
        , u'timestamp':firestore.SERVER_TIMESTAMP
    }
    db.collection(u'users').add(data)
    
    #msg_count()関数にテキストを引数で渡してcountに格納
    count = msg_count(event.message.text, profile.user_id)

    
    #「始める」と打つと最初の質問を送信
    if event.message.text == '始める' or event.message.text == 'はじめる':
        result = '質問を始めます。 \n今やっていることは？？(仕事や趣味など)'

    elif event.message.text == 'はい':
        result = 'お疲れ様でした!\n過去の体験をもとに目標を設定しよう!!\n\nまた始める時は『始める』を入力してね!'      

    elif event.message.text == 'いいえ':
        result = '自己分析を続ける？？\n始める or 終わる'

    elif event.message.text == '終わる' or event.message.text == 'おわる':
        result = 'また始める時は『始める』を入力してね！'


    #質問
    elif count == 1:
        result = 'なぜそれをやっているの？？'
        
    elif count == 2:
        result = 'なぜそう思ったの？？'

    elif count == 3:
        result = 'いつからそう思ったの？？\nそのきっかけは？？'

    elif count == 4:
        result = '原体験は見つかった？？\n『はい』 または 『いいえ』を入力してください。'


    #resultを返信
    line_bot_api.reply_message(              
        event.reply_token,
        TextSendMessage(text=result)
        )


if __name__ == "__main__":
    app.run()

import discord
from discord.ext import commands
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import traceback
import pymysql

# TODO: 스타일 리팩터링
'''
주석도 쫌 달고
너무 긴건 줄바꿈도 좀 해서
전체적으로 일관성있게
딱 읽기좋게
쿼리도 싹다 줄바꿈 잘 하셈
로그 구조도 확실하게 하나로 맞춰서
함수 시작할 때 시작 로그                               # utils 모듈로 뻄
중간에 에러나면 예외에다 에러났다고 응답하고 로그      # utils 모듈로 뻄
성공 실패 있는 명령어면 성공실패 로그에 찍고 이유      # utils 모듈로 뻄
시작할 때 \n찍어서 매개변수 보여주면 됨                # utils 모듈로 뻄
로그가 중요함 레벨도 딱 정확한 기준을 잡고 리팩터링 해야함
내용도 그렇고
'''

# TODO: utill모듈 만들기
'''
재사용성 생각해서 로그나 에러같은거 만들기
로그는 로그 발생지 에러인지 뭔지 시작인지 끝인지 어쩌구 그런거 보기
위에 "utils 모듈로 뺌"되있는거 보고 저런 상황에 쓰일 로그 만들기
에러 처리는 메시지 보내는 정도 될듯 이거도 재사용성보고 나중에 짤 때 생각하면 됨
디버그 로그같은거 있음 좋을듯 테스트 로그처럼 해서 테스트로 이거 None인가 아닌가 뭐가들어가나 싶을 때 찍는거
내가 개좋아하는 :::같은거 넣어서 하면 될듯
사용자가 db에 존재하는지 검증하는 함수 만들기
'''

# TODO: 핸들러 만들기
'''
cursor.execute호출 시 요청된 쿼리와 응답을 로그에 기록
'''

is_infologging = True if input("로그 레벨을 INFO로 설정하시겠습니까? (Y/N): ").lower() in ['y', 'Y'] else False

# 로그 디렉토리 생성
os.makedirs("logs", exist_ok=True)

# 로그 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] ::: %(module)s.%(funcName)s:%(lineno)d >>> %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_log_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', mode='w'),
        logging.StreamHandler()
    ]
)

if is_infologging:
    logging.getLogger().handlers[1].setLevel(logging.INFO)  # StreamHandler의 로그 레벨을 INFO로 설정

# 토큰 로드
load_dotenv()
TOKEN = os.environ.get('TOKEN')
PASSWORD = os.environ.get('PASSWORD')
if TOKEN:
    logging.debug("토큰이 성공적으로 로드되었습니다.")
else:
    logging.error("토큰이 로드되지 않았습니다.")
    raise EnvironmentError()
if PASSWORD:
    logging.debug("암호가 성공적으로 로드되었습니다.")
else:
    logging.error("암호가 로드되지 않았습니다.")
    raise EnvironmentError()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

bot.shared_data = {}

@bot.event
async def on_ready():
        activity = discord.Activity(
            name="봇 초기화중...",
            type=discord.ActivityType.playing
        )
        await bot.change_presence(activity=activity)

        # cogs 로드
        await load_cogs()

        db = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            passwd=PASSWORD,
            db='lumiel_data',
            charset='utf8'
        )
        cursor = db.cursor()

        bot.shared_data = {
            "GUILD_ID": 1383768206635962501,                     # 서버 ID
            "ENTRY_LOG_CHANNEL_ID": 1384501387211313222,         # 입장 로그 채널 ID
            "CHECK_MESSAGE_ID": 1388526152351744061,             # 인증 메시지 ID
            "PEOPLE_COUNT_CHANNEL_ID": 1388573766719901796,      # 인원수 채널 ID
            "event_message_id": int,                             # 이벤트 메시지 ID
            "INVITE_LOG_CHANNEL_ID": 1390313743564406785,        # 초대로그 채널 ID
            "CURSOR": cursor,                                    # DB 커서
            "PROMOTION_LOG_CHANNEL_ID": 1384518652841295912,     # 승급 로그 채널 ID
            "BEN_LOG_CHANNEL_ID": 1398123190999580672,           # 벤 로그 채널 ID
            "DB": db,                                            # DB 연결 객체
            "is_auction": False,                                 # 경매 활성화 여부
            "current_price": 0,                                  # 현재 경매 가격
            "increase_amount_price": 0,                          # 경매 상승폭
            "winner_id": 0                                       # 낙찰자 id
        }

        await bot.tree.sync()
        for command in bot.tree.get_commands():
            logging.debug(f"Command: {command.name}")

        # 업데이트/유지보수 중일 때
        activity = discord.Activity(
        name="업데이트중 | 원활한 이용이 어렵습니다.",
        type=discord.ActivityType.playing
        )
        status = discord.Status.dnd
        await bot.change_presence(activity=activity, status=status)

        # 봇의 상태에서 activity를 제거 (업데이트일땐 X)
        await bot.change_presence(activity=None)
        logging.info(f"{bot.user.name} 봇이 성공적으로 초기화되었습니다.")

async def load_cogs():
    try:
        await bot.load_extension("cogs.events")
        await bot.load_extension("cogs.commands.admin_command")
        await bot.load_extension("cogs.commands.event_command")
        await bot.load_extension("cogs.commands.data_command")
        await bot.load_extension("cogs.commands.experience_command")
        await bot.load_extension("cogs.commands.item_command")
        await bot.load_extension("cogs.commands.invite_command")
        logging.info("cogs가 성공적으로 로드되었습니다.")
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f"Cog 로드 중 오류 발생:\n {tb}")
        await bot.close()

bot.run(TOKEN)
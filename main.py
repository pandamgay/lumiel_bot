import discord
from discord.ext import commands
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import traceback
import pymysql
from utils import my_logger as ml
from utils import my_curser as mc

is_info_logging = True if input("로그 레벨을 INFO로 설정하시겠습니까? (Y/N): ").lower() in ['y', 'Y'] else False

logger = ml.MyLogger(is_info_logging)
my_logger = logger.initLogger()

# 토큰 로드
load_dotenv()
TOKEN = os.environ.get('TOKEN')
PASSWORD = os.environ.get('PASSWORD')
if TOKEN:
    my_logger.debug("토큰이 성공적으로 로드되었습니다.")
else:
    my_logger.error("토큰이 로드되지 않았습니다.")
    raise EnvironmentError()
if PASSWORD:
    my_logger.debug("암호가 성공적으로 로드되었습니다.")
else:
    my_logger.error("암호가 로드되지 않았습니다.")
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

        db = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            passwd=PASSWORD,
            db='lumiel_data',
            charset='utf8',
            cursorclass=mc.MyCursor  # 커서 클래스 사용
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
            "winner_id": 0,                                      # 낙찰자 ID
            "LOGGER": my_logger
        }

        # cogs 로드
        await load_cogs()

        await bot.tree.sync()
        for command in bot.tree.get_commands():
            my_logger.debug(f"Command: {command.name}")

        # 업데이트/유지보수 중일 때
        # activity = discord.Activity(
        # name="업데이트중 | 원활한 이용이 어렵습니다.",
        # type=discord.ActivityType.playing
        # )
        # status = discord.Status.dnd
        # await bot.change_presence(activity=activity, status=status)

        # 봇의 상태에서 activity를 제거 (업데이트일땐 X)
        await bot.change_presence(activity=None)
        my_logger.info(f"{bot.user.name} 봇이 성공적으로 초기화되었습니다.")

async def load_cogs():
    try:
        await bot.load_extension("cogs.events")
        await bot.load_extension("cogs.commands.admin_command")
        await bot.load_extension("cogs.commands.event_command")
        await bot.load_extension("cogs.commands.data_command")
        await bot.load_extension("cogs.commands.experience_command")
        await bot.load_extension("cogs.commands.item_command")
        await bot.load_extension("cogs.commands.invite_command")
        my_logger.info("cogs가 성공적으로 로드되었습니다.")
    except Exception as e:
        tb = traceback.format_exc()
        my_logger.error(f"Cog 로드 중 오류 발생:\n {tb}")
        await bot.close()

bot.run(TOKEN)

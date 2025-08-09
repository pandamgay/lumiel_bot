import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback
import random

class EventCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.my_logger = bot.shared_data["LOGGER"]

    @app_commands.command(name="이벤트-생성", description="이벤트를 생성합니다.")
    @app_commands.describe(
        제목="이벤트 제목을 입력하세요.",
        설명1="이벤트에 대한 설명을 입력하세요.",
        설명2="추가 설명을 입력하세요. (선택사항)",
        설명3="추가 설명을 입력하세요. (선택사항)"
    )
    @app_commands.default_permissions(administrator=True)
    async def createEvent(self, interaction: discord.Interaction, 제목: str, 설명1: str, 설명2: str = "", 설명3: str = ""):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        await interaction.response.send_message(
            f"# 이벤트 안내🎁: {제목}\n"
            f"{설명1}\n"
            f"{설명2}\n"
            f"{설명3}\n"
            f"이 메시지에 ✅를 눌러주시면 이벤트 참여가 완료됩니다.\n"
            f"@everyone"
        )
        sent_message = await interaction.original_response()
        shared["event_message_id"] = sent_message.id
        await sent_message.add_reaction("✅")

        self.my_logger.info(f"이벤트-생성 사용됨 - {user}\n message_id: {sent_message.id}")

    @app_commands.command(name="이벤트-종료", description="이벤트를 종료합니다.")
    @app_commands.default_permissions(administrator=True)
    async def finishEvent(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        guild = self.bot.get_guild(shared["GUILD_ID"])
        shared["event_message_id"] = None  # 이벤트 메시지 ID 초기화
        await interaction.response.defer()

        role = guild.get_role(1388778507617964084) # 역할 가져오기
        self.my_logger.debug(role)
        members_with_role = [member for member in guild.members if role in member.roles] # 역할을 가진 멤버만 필터링

        # 역할 제거
        for member in members_with_role:
            try:
                await member.remove_roles(role)
                self.my_logger.info(f"{member.display_name}에게서 역할 '{role.name}'을 성공적으로 제거했습니다.")
            except discord.Forbidden:
                self.my_logger.error(f"{member.display_name}에게서 역할을 제거할 수 없습니다. 권한을 확인해주세요.")
            except Exception as e:
                tb = traceback.format_exc()
                self.my_logger.error(f"{member.display_name}에게서 역할 제거 중 오류 발생: {tb}")
        await interaction.followup.send(
            f"# 이벤트 종료\n"
            f"현재 이벤트가 종료되었습니다. 참여해주신 모든 분들께 감사합니다.\n{role.mention}"
        )
        self.my_logger.info(f"이벤트-종료 사용됨 - {user}")

    @app_commands.command(name="이벤트-지정", description="이벤트를 직접 지정합니다.")
    @app_commands.default_permissions(administrator=True)
    async def choiceEvent(self, interaction: discord.Interaction, 이벤트id: str):
        이벤트id = int(이벤트id)
        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        shared["event_message_id"] = 이벤트id

        await interaction.response.send_message("성공적으로 이벤트id가 지정 되었습니다.", ephemeral=True)
        self.my_logger.info(f"이벤트-지정 사용됨 - {user}\n 지정된 이벤트 ID: {이벤트id}")

    @app_commands.command(name="랜덤추첨", description="이벤트 참여자중 랜덤으로 추첨합니다.")
    @app_commands.default_permissions(administrator=True)
    async def randomPeople(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        guild = self.bot.get_guild(shared["GUILD_ID"])

        role = guild.get_role(1388778507617964084) # 역할 가져오기
        self.my_logger.debug(role)
        members_with_role = [member for member in guild.members if role in member.roles] # 역할을 가진 멤버만 필터링

        if not members_with_role:
            await interaction.response.send_message(
                "현재 이벤트 참여자가 없습니다. 이벤트 참여자를 먼저 모집해주세요.", ephemeral=True
            )
            self.my_logger.info(f"랜덤추첨 사용 실패 - {user}\n이벤트 참여자가 없음")
            return

        # 랜덤 추첨
        winner = random.choice(members_with_role)
        await interaction.response.send_message(
            f"# 추첨 결과🎉\n"
            f"{winner.display_name} 님이 당첨되었습니다!\n"
            f"{winner.mention}"
        )

        self.my_logger.info(f"랜덤추첨 사용됨 - {user}\n 당첨자: {winner.display_name}({winner.id})")

async def setup(bot):
    self = EventCommand(bot)
    await bot.add_cog(EventCommand(bot))
    self.my_logger.debug("EventCommand cog가 성공적으로 로드되었습니다.")

import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback

class InviteCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_logger = bot.shared_data["LOGGER"]

    @app_commands.command(name="초대정보-추가", description="사용자의 초대정보를 추가합니다.")
    @app_commands.describe(초대자="초대자를 입력하세요.", 초대된_유저="초대된 멤버를 입력하세요.")
    @app_commands.default_permissions(administrator=True)
    async def addInviteInfo(self, interaction: discord.Interaction, 초대자: discord.Member, 초대된_유저: discord.Member):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]
        inviter_id = 초대자.id
        invited_member_id = 초대된_유저.id
        self.my_logger.info(f"초대정보-추가 사용됨 - {user}\n 초대자: {inviter_id}, 초대된 유저: {invited_member_id}")

        try:
            cursor.execute(
                f"SELECT * "
                f"FROM users "
                f"WHERE discord_user_id = {invited_member_id};"
            ) # 사용자 중복 확인
            result = cursor.fetchone()

            if result == None:
                self.my_logger.warning(f"초대된 유저가 DB에 존재하지 않음. - {user}")
                await interaction.response.send_message("초대된 유저가 DB에 존재하지 않습니다.", ephemeral=True)
                return

            cursor.execute(
                f"UPDATE users "
                f"SET inviter_id = {inviter_id} "
                f"WHERE user_id = {invited_member_id};"
            ) # 초대된 유저의 초대자 정보를 저장
            cursor.execute(
                f"UPDATE users "
                f"SET invite_count = invite_count + 1 "
                f"WHERE discord_user_id = {inviter_id};"
            ) # 초대자의 초대 횟수 증가
            cursor.execute(
                f"UPDATE users "
                f"SET experience = experience + 100 "
                f"WHERE discord_user_id = {inviter_id};"
            ) # 초대자 경험치 부여
            db.commit()
            await interaction.response.send_message(f"{초대된_유저.mention}의 초대정보가 저장되었습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"초대정보-추가 오류 발생: {tb}")
            await interaction.response.send_message(f"오류가 발생했습니다.\n {tb}")
            return


async def setup(bot):
    self = InviteCommand(bot)
    await bot.add_cog(InviteCommand(bot))
    self.my_logger.debug("InviteCommand cog가 성공적으로 로드되었습니다.")

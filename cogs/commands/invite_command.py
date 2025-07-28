import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback

class InviteCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        logging.info(f"초대정보-추가 사용됨 - {user}\n 초대자: {inviter_id}, 초대된 유저: {invited_member_id}")

        try:
            cursor.execute(f"SELECT * FROM users WHERE discord_user_id = {invited_member_id};")
            result = cursor.fetchone()

            if result == None:
                logging.warning(f"초대된 유저가 DB에 존재하지 않음. - {user}")
                await interaction.response.send_message("초대된 유저가 DB에 존재하지 않습니다.", ephemeral=True)
                return

            cursor.execute(f"UPDATE users SET inviter_id = {inviter_id} WHERE user_id = {invited_member_id};")
            cursor.execute(f"UPDATE users SET experience = invite_count + 1 WHERE discord_user_id = {inviter_id};")
            cursor.execute(f"UPDATE users SET experience = experience + 20 WHERE discord_user_id = {inviter_id};")
            db.commit()
            await interaction.response.send_message(f"{초대된_유저.mention}의 초대정보가 저장되었습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"초대정보-추가 오류 발생: {tb}")
            await interaction.response.send_message(f"오류가 발생했습니다.\n {tb}")
            return


async def setup(bot):
    await bot.add_cog(InviteCommand(bot))
    logging.debug("InviteCommand cog가 성공적으로 로드되었습니다.")
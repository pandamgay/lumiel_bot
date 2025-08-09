import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback

class ExperienceCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.my_logger = bot.shared_data["LOGGER"]

    @app_commands.command(name="경험치-부여", description="사용자에게 경험치를 부여합니다.")
    @app_commands.default_permissions(administrator=True)
    async def addExperience(self, interaction: discord.Interaction, 유저: discord.Member, 경험치: int):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]

        # 경험치 부여
        if 경험치 < 0:
            await interaction.response.send_message("경험치는 0 이상의 값이어야 합니다.", ephemeral=True)
            return
        try:
            cursor.execute(
                f"UPDATE users "
                f"SET experience = experience + {경험치} "
                f"WHERE discord_user_id = {유저.id};"
            ) # 경험치 부여
            db.commit()
            self.my_logger.info(
                f"경험치-부여 사용됨 - {user}\n"
                f"유저: {유저.display_name}({유저.id}), 경험치: {경험치}"
            )
            await interaction.response.send_message(f"{유저.mention}에게 {경험치} 경험치를 부여했습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경험치 부여 중 오류 발생: {tb}")
            await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
            return

    @app_commands.command(name="경험치-삭제", description="사용자에게 경험치를 삭제합니다.")
    @app_commands.default_permissions(administrator=True)
    async def deleteExperience(self, interaction: discord.Interaction, 유저: discord.Member, 경험치: int):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]

        # 경험치 검증
        try:
            cursor.execute(
                f"SELECT experience "
                f"FROM users "
                f"WHERE discord_user_id = {유저.id};"
            )  # 사용자 경험치 조회
            result = cursor.fetchone()
            if result is None:
                await interaction.response.send_message(
                    "해당 사용자가 존재하지 않습니다.", ephemeral=True
                )
                self.my_logger.warning(f"경험치-삭제 사용실패 - {user}")
                return
            if result[0] - 경험치 < 0:
                await interaction.response.send_message(
                    f"{유저.mention}의 경험치가 부족합니다.", ephemeral=True
                )
                self.my_logger.warning(f"경험치-삭제 사용실패 - {user}")
                return
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경험치 조회 중 오류 발생: {tb}")
            await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
            return

        # 경험치 삭제
        if 경험치 < 0:
            await interaction.response.send_message("경험치는 0 이상의 값이어야 합니다.", ephemeral=True)
            self.my_logger.warning(f"경험치-삭제 사용실패 - {user}")
            return
        try:
            # 사용자 정보 업데이트
            cursor.execute(
                f"UPDATE users "
                f"SET experience = experience - {경험치} "
                f"WHERE discord_user_id = {유저.id};"
            )  # 경험치 삭제
            db.commit()
            self.my_logger.info(
                f"경험치-삭제 사용됨 - {user}\n"
                f"유저: {유저.display_name}({유저.id}), 경험치: -{경험치}"
            )
            await interaction.response.send_message(f"{유저.mention}에게 {경험치} 경험치를 삭제했습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경험치 삭제 중 오류 발생: {tb}")
            await interaction.response.send_message("오류가 발생했습니다.",ephemeral=True)
            return

    @app_commands.command(name="유저-경험치-조회", description="사용자의 경험치를 조회합니다.")
    @app_commands.describe(유저="경험치를 조회할 사용자를 선택하세요.")
    @app_commands.default_permissions(administrator=True)
    async def checkExperience(self, interaction: discord.Interaction, 유저: discord.Member):

        shared = self.bot.shared_data
        cursor = shared["CURSOR"]
        user = f"{interaction.user.display_name}[{interaction.user.id}]"

        try:
            cursor.execute(
                f"SELECT experience "
                f"FROM users "
                f"WHERE discord_user_id = {유저.id};"
            )  # 사용자 경험치 조회
            result = cursor.fetchone()
            if result is None:
                await interaction.response.send_message(
                    f"{유저.mention}의 경험치를 찾을 수 없습니다.", ephemeral=True
                )
                self.my_logger.warning(
                    f"경험치-조회 실패 - {user}\n"
                    f"유저: {유저.display_name}({유저.id})"
                )
                return
            경험치 = result[0]
            await interaction.response.send_message(f"{유저.mention}의 경험치는 {경험치}입니다.")
            self.my_logger.info(
                f"경험치-조회 사용됨 - {user}\n"
                f"유저: {유저.display_name}({유저.id}), 경험치: {경험치}"
            )
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경험치 조회 중 오류 발생: {tb}")
            await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)

    @app_commands.command(name="경험치-조회", description="자신의 경험치를 조회합니다.")
    async def myExperience(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        cursor = shared["CURSOR"]
        db = shared["DB"]
        user = f"{interaction.user.display_name}[{interaction.user.id}]"

        try:
            cursor.execute(
                f"SELECT experience "
                f"FROM users "
                f"WHERE discord_user_id = {interaction.user.id};"
            ) # 경험치 조회
            result = cursor.fetchone()
            if result is None:
                await interaction.response.send_message(
                    "당신의 경험치를 찾을 수 없습니다. "
                    "운영진에게 문의해주세요.",
                    ephemeral=True
                )
                self.my_logger.warning(f"경험치-조회 실패 - {user}")
                return
            경험치 = result[0]
            await interaction.response.send_message(f"당신의 경험치는 {경험치}입니다.", ephemeral=True)
            self.my_logger.info(f"경험치-조회 사용됨 - {user}, 경험치: {경험치}")
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경험치 조회 중 오류 발생: {tb}")
            await interaction.response.send_message(
                "오류가 발생했습니다. 운영진에게 문의해주세요.", ephemeral=True
            )

async def setup(bot):
    self = ExperienceCommand(bot)
    await bot.add_cog(ExperienceCommand(bot))
    self.my_logger.debug("ExperienceCommand cog가 성공적으로 로드되었습니다.")

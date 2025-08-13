import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback
from datetime import datetime, timedelta
from discord.ui import Button, View
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class AdminCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.checkWarn, CronTrigger(hour=0, minute=0))  # 매일 12:00 AM 실행
        self.scheduler.start()
        self.my_logger = bot.shared_data["LOGGER"]

    @app_commands.command(name="현재인원-새로고침", description="현재 인원을 새로고침합니다.")
    @app_commands.default_permissions(administrator=True)
    async def refreshPeopleCount(self, interaction: discord.Interaction):
        shared = self.bot.shared_data
        guild = self.bot.get_guild(shared["GUILD_ID"])
        channel_id = shared["PEOPLE_COUNT_CHANNEL_ID"]
        user = f"{interaction.user.display_name}[{interaction.user.id}]"

        # 음성 채널 가져오기
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                self.my_logger.error(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
                raise ValueError(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
            self.my_logger.debug(f"음성 채널: {bool(channel)}")
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"음성 채널을 가져오는 중 오류 발생: {tb}")
            return

        # 음성 채널 이름 변경
        try:
            new_name = f"현재 인원: {guild.member_count}명 📡"
            await channel.edit(name=new_name)
            self.my_logger.info(f"음성 채널 이름을 '{new_name}'으로 성공적으로 변경했습니다.")
        except discord.Forbidden:
            self.my_logger.error("음성 채널 이름을 변경할 권한이 없습니다. 권한을 확인해주세요.")
            return
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"음성 채널 이름 변경 중 오류 발생: {tb}")
            return

        await interaction.response.send_message("성공적으로 새로고침 되었습니다.", ephemeral=True)
        self.my_logger.info(f"현재인원-새로고침이 사용됨 - {user}")

    @app_commands.command(name="경고-부여", description="유저에게 경고를 부여합니다.")
    @app_commands.describe(
        유저="경고를 부여할 유저",
        사유="경고 사유",
        기간="경고 기간 (기본값: 30일)"
    )
    @app_commands.default_permissions(administrator=True)
    async def addWarn(self, interaction: discord.Interaction, 유저: discord.Member, 사유: str, 기간: int = 30):

        shared = self.bot.shared_data
        cursor = shared["CURSOR"]
        db = shared["DB"]
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        channel = self.bot.get_channel(shared["BEN_LOG_CHANNEL_ID"])
        guild = interaction.guild
        self.my_logger.info(
            f"경고-부여 사용됨 - {user}\n"
            f"유저: {유저.display_name}({유저.id}), 사유: {사유}, 기간: {기간}일"
        )
        role = guild.get_role(1398122039776383038)
        self.my_logger.debug(role)

        if not role:
            self.my_logger.error("경고 역할을 찾을 수 없습니다. 역할 ID를 확인해주세요.")
            await interaction.response.send_message(
                "**[error}** 경고 역할을 찾을 수 없습니다.", ephemeral=True
            )
            return
        try:
            if role in 유저.roles:
                self.my_logger.warning(f"{유저.display_name}({유저.id})는 이미 경고 역할을 가지고 있습니다.")
                await interaction.response.send_message(
                    f"{유저.mention}님은 이미 경고 역할을 가지고 있습니다.\n"
                    f"2회 경고는 밴 대상입니다. 조치 바랍니다.", ephemeral=True
                )
                return
            await 유저.add_roles(role)
            self.my_logger.info(f"{유저.display_name}({유저.id})에게 경고 역할을 성공적으로 부여했습니다.")
            until = datetime.now() + timedelta(days=기간)
            fomatted_time = until.strftime("%Y-%m-%d")
            cursor.execute(
                f"UPDATE users "
                f"SET warn_until = '{fomatted_time}' "
                f"WHERE discord_user_id = {유저.id};"
            ) # 경고 기간 저장
            db.commit()
            await channel.send(
                f"# 경고\n"
                f"유저: {유저.mention}\n"
                f"사유: {사유}\n"
                f"기간: {기간}일\n"
                f"자세한 사항은 {interaction.user.mention}님에게 문의해주세요."
            )
            await interaction.response.send_message(f"{유저.mention}님에게 경고를 부여했습니다.")
        except discord.Forbidden:
            self.my_logger.error("경고 역할을 부여할 권한이 없습니다. 권한을 확인해주세요.")
            await interaction.response.send_message(
                "**[error]** 경고 역할을 부여할 권한이 없습니다.", ephemeral=True
            )
            return
        except Exception as e:
            tb = traceback.format_exc()
            self.my_logger.error(f"경고 역할 부여 중 오류 발생: {tb}")
            await interaction.response.send_message(
                "**[error]** 경고 역할 부여 중 오류가 발생했습니다.", ephemeral=True
            )
            return

    @app_commands.command(
        name="봇-종료",
        description="봇을 종료합니다.(위험한 명령어이므로 신중하게 사용하세요.)"
    )
    @app_commands.default_permissions(administrator=True)
    async def shutdown(self, interaction: discord.Interaction):

        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        yes_button = Button(label="예", style=discord.ButtonStyle.danger)
        no_button = Button(label="아니오", style=discord.ButtonStyle.secondary)
        self.my_logger.info(f"봇-종료 사용됨 - {user}")

        async def yes_callback(interaction: discord.Interaction):
            conn = self.bot.shared_data["DB"]
            await message.delete()
            await interaction.channel.send("봇을 종료합니다.")
            conn.close()
            self.my_logger.info("봇이 종료됩니다.")
            await self.bot.close()

        async def no_callback(interaction: discord.Interaction):
            await message.delete()
            await interaction.channel.send("봇 종료가 취소되었습니다.")
            self.my_logger.info("봇 종료가 취소되었습니다.")

        yes_button.callback = yes_callback
        no_button.callback = no_callback

        view = View()
        view.add_item(yes_button)
        view.add_item(no_button)

        await interaction.response.defer()
        message = await interaction.followup.send(
            "봇을 정말로 종료하시겠습니까? 이 작업은 되돌릴 수 없습니다.", view=view
        )
        self.my_logger.debug(f"message: {message.id}")

    @app_commands.command(
        name="경고-갱신",
        description="경고가 만료된 유저를 갱신합니다.(매일 정오에 작동되므로 가급적 사용하지 마세요.)"
    )
    @app_commands.default_permissions(administrator=True)
    async def enforcementCheckWarn(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        cursor = shared["CURSOR"]
        db = shared["DB"]
        channel = self.bot.get_channel(shared["BEN_LOG_CHANNEL_ID"])
        guild = self.bot.get_guild(shared["GUILD_ID"])
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        role = guild.get_role(1398122039776383038)
        self.my_logger.info(f"경고-갱신 사용됨 - {user}")
        self.my_logger.debug(role)

        members_with_role = [member for member in guild.members if role in member.roles]
        if not members_with_role:
            self.my_logger.info("경고 역할을 가진 사용자가 없습니다.")
            await interaction.response.send_message("현재 경고 역할을 가진 사용자가 없습니다.", ephemeral=True)
            return

        i = 0
        j = 0
        k = 0
        for member in members_with_role:
            try:
                i += 1
                cursor.execute(
                    f"SELECT warn_until "
                    f"FROM users "
                    f"WHERE discord_user_id = {member.id}"
                ) #  경고 기간 조회
                result = cursor.fetchone()[0]
                current_date = datetime.today().date()
                if result < current_date:
                    k += 1
                    await member.remove_roles(role)
                    self.my_logger.debug(f"{member.display_name}의 경고 역할이 제거되었습니다.")
                    await channel.send(f"{member.mention}님의 경고가 만료되어 경고 역할이 제거되었습니다.")
            except Exception as e:
                tb = traceback.format_exc()
                self.my_logger.error(f"경고 확인 중 오류 발생: {tb}")
                j += 1
        self.my_logger.info(
            f"경고 확인 완료 - {i}명의 유저 중 {k}명의 경고가 만료되었고, "
            f"{j}명의 유저에서 오류가 발생했습니다."
        )
        await interaction.response.send_message(
            f"경고 갱신이 완료되었습니다.\n"
            f"{i}명의 유저 중 {k}명의 경고가 만료되었고, {j}명의 유저에서 오류가 발생했습니다."
        )

    async def checkWarn(self):

        shared = self.bot.shared_data
        cursor = shared["CURSOR"]
        db = shared["DB"]
        channel = self.bot.get_channel(shared["BEN_LOG_CHANNEL_ID"])
        guild = self.bot.get_guild(shared["GUILD_ID"])
        role = guild.get_role(1398122039776383038)
        self.my_logger.debug(role)

        members_with_role = [member for member in guild.members if role in member.roles]
        if not members_with_role:
            self.my_logger.info("경고 역할을 가진 사용자가 없습니다.")
            return

        i = 0
        j = 0
        k = 0
        for member in members_with_role:
            try:
                i += 1
                cursor.execute(
                    f"SELECT warn_until "
                    f"FROM users "
                    f"WHERE discord_user_id = {member.id}"
                ) # 경고 기간 조회
                result = cursor.fetchone()[0]
                current_date = datetime.today().date()
                if result < current_date:
                    k += 1
                    await member.remove_roles(role)
                    self.my_logger.debug(f"{member.display_name}의 경고 역할이 제거되었습니다.")
                    channel.send(f"{member.mention}님의 경고가 만료되어 경고 역할이 제거되었습니다.")
            except Exception as e:
                tb = traceback.format_exc()
                self.my_logger.error(f"경고 확인 중 오류 발생: {tb}")
                j += 1
        self.my_logger.info(
            f"경고 확인 완료 - {i}명의 유저 중 {k}명의 경고가 만료되었고, "
            f"{j}명의 유저에서 오류가 발생했습니다."
        )


async def setup(bot):
    self = AdminCommand(bot)
    await bot.add_cog(AdminCommand(bot))
    self.my_logger.debug("AdminCommand cog가 성공적으로 로드되었습니다.")

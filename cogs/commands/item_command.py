import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback
import random
import time
from datetime import datetime, timedelta

class ItemCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def autocomplete_options(self, interaction: discord.Interaction, 배율: str):
        options = [
            app_commands.Choice(name="2배", value="2배"),
            app_commands.Choice(name="5배", value="5배"),
        ]
        # 현재 입력된 값과 일치하는 옵션 필터링
        return [option for option in options if 배율.lower() in option.name.lower()]

    @app_commands.command(name="경험치-도박", description="경험치를 도박합니다.")
    @app_commands.describe(배율="배율을 입력하세요. 2배: 1/2, 5배: 1/5", 경험치="도박할 경험치 양을 입력하세요. 2배: ~ 200, 5배: ~ 50")
    @app_commands.autocomplete(배율=autocomplete_options)
    async def gambleExperience(self, interaction: discord.Interaction, 배율: str, 경험치: int):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]
        await interaction.response.defer()

        # 배율 검증
        if 배율 not in ["2배", "5배"]:
            await interaction.followup.send("배율은 '2배' 또는 '5배'만 가능합니다.")
            logging.warning(f"경험치-도박 사용실패 - {user}\n 배율: {배율}, 경험치: {경험치}")
            return

        # 경험치 검증
        if 배율 == "2배" and 경험치 > 200:
            await interaction.followup.send("2배 도박은 최대 200 경험치까지만 가능합니다.")
            logging.warning(f"경험치-도박 사용실패 - {user}\n 배율: {배율}, 경험치: {경험치}")
            return
        elif 배율 == "5배" and 경험치 > 50:
            await interaction.followup.send("5배 도박은 최대 50 경험치까지만 가능합니다.")
            logging.warning(f"경험치-도박 사용실패 - {user}\n 배율: {배율}, 경험치: {경험치}")
            return

        # 게임 시작
        try:
            cursor.execute(f"SELECT experience FROM users WHERE discord_user_id = {interaction.user.id};")
            result = cursor.fetchone()
            if result is None or result[0] < 경험치:
                await interaction.followup.send("경험치가 부족합니다.")
                logging.warning(f"경험치-도박 사용실패 경험치 부족 - {user}\n 배율: {배율}, 경험치: {경험치}")
                return

            # 경험치 차감
            cursor.execute(f"UPDATE users SET experience = experience - {경험치} WHERE discord_user_id = {interaction.user.id};")
            db.commit()

            # 도박 결과
            random.seed(time.time())
            if 배율 == "2배":
                win = random.choice([True, False]) # 1/2
            else:
                win = random.choice([True, False, False, False, False]) # 1/5
            if win:
                if 배율 == "2배":
                    price = 경험치 * 2
                else:
                    price = 경험치 * 5

                cursor.execute(f"UPDATE users SET experience = experience + {price} WHERE discord_user_id = {interaction.user.id};")
                db.commit()
                time.sleep(2)
                await interaction.followup.send(f"축하합니다! {price} 경험치를 획득했습니다.🎉🎉 현재 경험치: {result[0] + price}")
                logging.info(f"경험치-도박 사용됨 승리 - {user}\n 배율: {배율}, 경험치: {경험치}")
            else:
                await interaction.followup.send(f"아쉽게도 도박에 실패했습니다.😭😭 현재 경험치: {result[0] - 경험치}")
                logging.info(f"경험치-도박 사용됨 실패 - {user}\n 배율: {배율}, 경험치: {경험치}")

        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"도박 중 오류 발생: {tb}")
            await interaction.followup.send("오류가 발생했습니다. 관리자에게 문의하세요.")

    @app_commands.command(name="출석-체크", description="출석을 기록합니다.")
    async def attendanceCheck(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]

        logging.info(f"출석-체크 사용됨 - {user}")

        # 출석 정보 가져오기
        cursor.execute(f"SELECT recent_attendance_date, continuous_attendance_date FROM users WHERE discord_user_id = {interaction.user.id};")
        result = cursor.fetchone()
        logging.debug(f"result ::: {result}")
        continuous_attendance_date = result[1] + 1

        current_time = datetime.now()
        fomatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        logging.debug(f"current_time - result[0] ::: {current_time - result[0]}")

        if current_time - result[0] < timedelta(hours=24):
            logging.debug("current_time - result[0] < timedelta(hours=24)")
            await interaction.response.send_message(f"24시간 이내에 출석을 기록했습니다."
                                                    f"다음 출석까지 {24 - (current_time - result[0]).seconds // 3600}시간 남았습니다.")
            logging.info(f"{user}는 이미 24시간 이내에 출석을 기록했습니다.")
            return
        elif current_time - result[0] > timedelta(hours=48):
            logging.debug("current_time - result[0] < timedelta(hours=48)")
            cursor.execute(f"UPDATE users SET continuous_attendance_date = 0 WHERE discord_user_id = {interaction.user.id};")
            continuous_attendance_date = 1

        cursor.execute(f"UPDATE users SET recent_attendance_date = '{fomatted_time}' WHERE discord_user_id = {interaction.user.id};")
        cursor.execute(f"UPDATE users SET continuous_attendance_date = continuous_attendance_date + 1 WHERE discord_user_id = {interaction.user.id};")
        cursor.execute(f"UPDATE users SET experience = experience + 10 WHERE discord_user_id = {interaction.user.id};")
        db.commit()

        await interaction.response.send_message(f"출석이 기록되었습니다! 10경험치가 지급되었고,\n"
                                                f"현재 {interaction.user.display_name}님의 연속출석 기록은 {continuous_attendance_date}일입니다!")

    @app_commands.command(name="진급-하기", description="등급을 올라갑니다.")
    async def promotion(self, interaction: discord.Interaction):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        guild = interaction.guild
        db = shared["DB"]
        channel = self.bot.get_channel(shared["PROMOTION_LOG_CHANNEL_ID"])

        logging.info(f"진급-하기 사용됨 - {user}")

        user_roles = [role.id for role in interaction.user.roles]
        logging.debug(user_roles)

        cursor.execute(f"SELECT experience FROM users WHERE discord_user_id = {interaction.user.id};")
        user_exp = cursor.fetchone()[0]

        member = guild.get_member(interaction.user.id)
        if member is None:
            logging.error(f"멤버를 찾을 수 없음: {interaction.user.id}")
            await interaction.response.send_message("오류가 발생했습니다. <@875257348178980875>에게 문의하세요.", ephemeral=True)
            return

        try:
            if 1383803534973075608 in user_roles:
                if user_exp < 5000:
                    logging.info(f"2단계 진급 실패 - {user}")
                    await interaction.response.send_message(f"현재 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                            f"필요 경험치: 5000, 현재 경험치: {user_exp}", ephemeral=True)
                    return
                cursor.execute(f"UPDATE users SET experience = experience - 5000 WHERE discord_user_id = {interaction.user.id};")
                db.commit()
                role1 = guild.get_role(1383804395720015923)
                role2 = guild.get_role(1383803534973075608)
                logging.debug(f"role1: {role1}, role2: {role2}")
                await member.add_roles(role1)
                await member.remove_roles(role2)
                logging.info(f"2단계 진급 성공 - {user}")
                await interaction.response.send_message(f"축하합니다! 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 5000}")
                await channel.send(f"{interaction.user.mention} 님이 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
            elif 1383804395720015923 in user_roles:
                if user_exp < 10000:
                    logging.info(f"3단계 진급 실패 - {user}")
                    await interaction.response.send_message(f"현재 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                            f"필요 경험치: 10000, 현재 경험치: {user_exp}", ephemeral=True)
                    return
                cursor.execute(
                    f"UPDATE users SET experience = experience - 10000 WHERE discord_user_id = {interaction.user.id};")
                db.commit()
                role1 = guild.get_role(1383804879734313058)
                role2 = guild.get_role(1383804395720015923)
                logging.debug(f"role1: {role1}, role2: {role2}")
                await member.add_roles(role1)
                await member.remove_roles(role2)
                logging.info(f"3단계 진급 성공 - {user}")
                await interaction.response.send_message(f"축하합니다! 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 10000}")
                await channel.send(f"{interaction.user.mention} 님이 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
            elif 1383804879734313058 in user_roles:
                logging.info(f"진급 실패 - {user}")
                await interaction.response.send_message(f"이미 최고 등급인 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷입니다.", ephemeral=True)
                return
            else:
                if user_exp < 2000:
                    logging.info(f"1단계 진급 실패 - {user}")
                    await interaction.response.send_message(f"현재 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                            f"필요 경험치: 2000, 현재 경험치: {user_exp}", ephemeral=True)
                    return
                cursor.execute(f"UPDATE users SET experience = experience - 2000 WHERE discord_user_id = {interaction.user.id};")
                db.commit()
                role = guild.get_role(1383803534973075608)
                logging.debug(f"role: {role}")
                await member.add_roles(role)
                logging.info(f"1단계 진급 성공 - {user}")
                await interaction.response.send_message(f"축하합니다! 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 2000}")
                await channel.send(f"{interaction.user.mention} 님이 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"진급 중 오류 발생: {tb}")
            await interaction.response.send_message("오류가 발생했습니다. <@875257348178980875>에게 문의하세요.")

async def setup(bot):
    await bot.add_cog(ItemCommand(bot))
    logging.debug("ItemCommand cog가 성공적으로 로드되었습니다.")
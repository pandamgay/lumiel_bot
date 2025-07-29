import logging
import discord
from discord.ext import commands
from discord import app_commands
import traceback
import random
import time
from datetime import datetime, timedelta
from discord.ui import Button, View

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
    @app_commands.describe(배율="배율을 입력하세요. 2배: 1/2, 5배: 1/5", 경험치="도박할 경험치 양을 입력하세요. 2배: ~ 100, 5배: ~ 50")
    @app_commands.autocomplete(배율=autocomplete_options)
    async def gambleExperience(self, interaction: discord.Interaction, 배율: str, 경험치: int):

        shared = self.bot.shared_data
        user = f"{interaction.user.display_name}[{interaction.user.id}]"
        cursor = shared["CURSOR"]
        db = shared["DB"]

        button1 = Button(label="빨간색🟥", style=discord.ButtonStyle.secondary)
        button1.callback = lambda interaction: button_callback(interaction, 1)

        button2 = Button(label="파란색🟦", style=discord.ButtonStyle.secondary)
        button2.callback = lambda interaction: button_callback(interaction, 2)

        button3 = Button(label="초록색🟩", style=discord.ButtonStyle.secondary)
        button3.callback = lambda interaction: button_callback(interaction, 3)

        button4 = Button(label="노란색🟨", style=discord.ButtonStyle.secondary)
        button4.callback = lambda interaction: button_callback(interaction, 4)

        button5 = Button(label="주황색🟧", style=discord.ButtonStyle.secondary)
        button5.callback = lambda interaction: button_callback(interaction, 5)

        await interaction.response.defer()
        logging.info(f"경험치-도박 사용됨 - {user}\n 배율: {배율}, 경험치: {경험치}")

        # 배율 검증
        if 배율 not in ["2배", "5배"]:
            await interaction.followup.send("배율은 '2배' 또는 '5배'만 가능합니다.")
            logging.warning(f"경험치-도박 사용실패 - {user}\n 배율: {배율}, 경험치: {경험치}")
            return

        # 경험치 검증
        if 배율 == "2배" and 경험치 > 100:
            await interaction.followup.send("2배 도박은 최대 100 경험치까지만 가능합니다.")
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

            async def button_callback(interaction: discord.Interaction, color: int):
                game_result = self.playGamble(배율, color, 경험치, interaction.user.id)
                logging.debug(f"color: {color}, game_result: {game_result}")
                logging.debug(f"game_result: {game_result}")
                match = {
                    1: "빨간색🟥",
                    2: "파란색🟦",
                    3: "초록색🟩",
                    4: "노란색🟨",
                    5: "주황색🟧"
                }
                color_result = match.get(game_result[2], "알 수 없는 색상")
                if game_result[0]:
                    await message.delete()
                    await interaction.channel.send(f"{interaction.user.mention}님, 축하합니다! {game_result[1]} 경험치를 획득했습니다!🎉🎉"
                                                   f"\n**현재 경험치: {result[0] + game_result[1]}**")
                else:
                    await message.delete()
                    await interaction.channel.send(f"{interaction.user.mention}님, 아쉽게도 도박에 실패했습니다.😭😭 결과는 {color_result}이었습니다."
                                                   f"\n**현재 경험치: {result[0] - 경험치}**")

            view = View()
            view.add_item(button1)
            view.add_item(button2)
            if 배율 == "5배":
                view.add_item(button3)
                view.add_item(button4)
                view.add_item(button5)

            message = await interaction.followup.send(f"{interaction.user.mention}님이 {배율} 도박을 시작합니다! 배팅할 색상을 선택하세요.", view=view)
            message = await interaction.channel.fetch_message(message.id)

        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"도박 중 오류 발생: {tb}")
            await interaction.followup.send("오류가 발생했습니다. 운영진에게 문의하세요.")

    def playGamble(self, odds: str, color: int, experience: int, user_id: int):
        cursor = self.bot.shared_data["CURSOR"]
        db = self.bot.shared_data["DB"]
        random.seed(time.time())

        if odds == "2배":
            win = random.choice([1, 2])
            if win == color:
                cursor.execute(f"UPDATE users SET experience = experience + {experience * 2} WHERE discord_user_id = {user_id};")
                db.commit()
                logging.info(f"도박 성공 - {experience * 2} 경험치를 획득했습니다.[playGamble]")
                return [True, experience * 2, win]
            else:
                logging.info(f"도박 실패 - {experience} 경험치를 잃었습니다.[playGamble]")
                return [False, 0, win]
        elif odds == "5배":
            win = random.choice([1, 2, 3, 4, 5])
            if win == color:
                cursor.execute(f"UPDATE users SET experience = experience + {experience * 5} WHERE discord_user_id = {user_id};")
                db.commit()
                logging.info(f"도박 성공 - {experience * 5} 경험치를 획득했습니다.[playGamble]")
                return [True, experience * 5, win]
            else:
                logging.info(f"도박 실패 - {experience} 경험치를 잃었습니다.[playGamble]")
                return [False, 0, win]

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
                                                    f"다음 출석까지 {24 - (current_time - result[0]).seconds // 3600}시간 남았습니다.", ephemeral=True)
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
        view = View()
        yes_button = Button(label="예", style=discord.ButtonStyle.primary)
        view.add_item(yes_button)
        no_button = Button(label="아니오", style=discord.ButtonStyle.secondary)
        view.add_item(no_button)
        await interaction.response.defer()

        logging.info(f"진급-하기 사용됨 - {user}")

        user_roles = [role.id for role in interaction.user.roles]
        logging.debug(user_roles)

        cursor.execute(f"SELECT experience FROM users WHERE discord_user_id = {interaction.user.id};")
        user_exp = cursor.fetchone()[0]

        member = guild.get_member(interaction.user.id)
        if member is None:
            logging.error(f"멤버를 찾을 수 없음: {interaction.user.id}")
            await interaction.followup.send("오류가 발생했습니다. <@875257348178980875>에게 문의하세요.")
            return

        if 1383803534973075608 in user_roles:
            if user_exp < 5000:
                logging.info(f"2단계 진급 실패 - {user}")
                await interaction.followup.send(f"현재 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                        f"필요 경험치: 5000, 현재 경험치: {user_exp}")
                return
            else:
                message = await interaction.followup.send(f"{interaction.user.mention} 님, 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급을 진행하시겠습니까?\n"
                                                    f"필요 경험치: 5000, 현재 경험치: {user_exp}", view=view)
        elif 1383804395720015923 in user_roles:
            if user_exp < 10000:
                logging.info(f"3단계 진급 실패 - {user}")
                await interaction.followup.send(f"현재 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                        f"필요 경험치: 10000, 현재 경험치: {user_exp}")
                return
            else:
                message = await interaction.followup.send(f"{interaction.user.mention} 님, 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급을 진행하시겠습니까?\n"
                                                        f"필요 경험치: 10000, 현재 경험치: {user_exp}", view=view)
        elif 1383804879734313058 in user_roles:
            logging.info(f"진급 실패 - {user}")
            await interaction.followup.send(f"이미 최고 등급인 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷입니다.")
            return
        else:
            if user_exp < 2000:
                logging.info(f"1단계 진급 실패 - {user}")
                await interaction.followup.send(f"현재 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급하기 위한 경험치가 부족합니다.\n"
                                                        f"필요 경험치: 2000, 현재 경험치: {user_exp}")
                return
            else:
                message = await interaction.followup.send(f"{interaction.user.mention} 님, 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급을 진행하시겠습니까?\n"
                                                        f"필요 경험치: 2000, 현재 경험치: {user_exp}", view=view)
        message = await interaction.channel.fetch_message(message.id)

        async def yes_callback(interaction: discord.Interaction):
            try:
                if 1383803534973075608 in user_roles:
                    await message.delete()
                    cursor.execute(f"UPDATE users SET experience = experience - 5000 WHERE discord_user_id = {interaction.user.id};")
                    db.commit()
                    role1 = guild.get_role(1383804395720015923)
                    role2 = guild.get_role(1383803534973075608)
                    logging.debug(f"role1: {role1}, role2: {role2}")
                    await member.add_roles(role1)
                    await member.remove_roles(role2)
                    logging.info(f"2단계 진급 성공 - {user}")
                    await interaction.channel.send(f"{interaction.user.mention}님, 축하합니다! 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 5000}")
                    await channel.send(f"{interaction.user.mention} 님이 𝓖𝓸𝓵𝓭. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
                elif 1383804395720015923 in user_roles:
                    await message.delete()
                    cursor.execute(
                        f"UPDATE users SET experience = experience - 10000 WHERE discord_user_id = {interaction.user.id};")
                    db.commit()
                    role1 = guild.get_role(1383804879734313058)
                    role2 = guild.get_role(1383804395720015923)
                    logging.debug(f"role1: {role1}, role2: {role2}")
                    await member.add_roles(role1)
                    await member.remove_roles(role2)
                    logging.info(f"3단계 진급 성공 - {user}")
                    await interaction.channel.send(f"{interaction.user.mention}님, 축하합니다! 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 10000}")
                    await channel.send(f"{interaction.user.mention} 님이 𝓘𝓶𝓹𝓮𝓻𝓲𝓪𝓵. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
                else:
                    await message.delete()
                    cursor.execute(f"UPDATE users SET experience = experience - 2000 WHERE discord_user_id = {interaction.user.id};")
                    db.commit()
                    role = guild.get_role(1383803534973075608)
                    logging.debug(f"role: {role}")
                    await member.add_roles(role)
                    logging.info(f"1단계 진급 성공 - {user}")
                    await interaction.channel.send(f"{interaction.user.mention}님, 축하합니다! 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급되었습니다! 현재 경험치: {user_exp - 2000}")
                    await channel.send(f"{interaction.user.mention} 님이 𝓼𝓲𝓵𝓿𝓮𝓻. 𝓭𝓻𝓪𝓰𝓸𝓷으로 진급했습니다!")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"진급 중 오류 발생: {tb}")
                await interaction.channel.send("오류가 발생했습니다. <@875257348178980875>에게 문의하세요.")
        async def no_callback(interaction: discord.Interaction):
            await interaction.channel.send("진급이 취소되었습니다.")
            logging.info(f"{user} 님이 진급을 취소했습니다.")

        yes_button.callback = yes_callback
        no_button.callback = no_callback

async def setup(bot):
    await bot.add_cog(ItemCommand(bot))
    logging.debug("ItemCommand cog가 성공적으로 로드되었습니다.")
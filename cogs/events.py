import discord
from discord.ext import commands
import logging
import traceback

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        logging.debug("on_raw_reaction_add실행됨")
        if payload.user_id == self.bot.user.id:
            return

        shared = self.bot.shared_data
        user = f"{payload.member.display_name}[{payload.user_id}]"
        user_roles = [role.name for role in payload.member.roles]
        entry_log_channel = self.bot.get_channel(shared["ENTRY_LOG_CHANNEL_ID"])
        guild = self.bot.get_guild(shared["GUILD_ID"])
        db = shared["DB"]
        cursor = shared["CURSOR"]

        # 반응한 메시지 확인
        if payload.message_id == shared["CHECK_MESSAGE_ID"]:
            logging.debug(f"{user}가 인증 메시지에 반응했습니다.")
            # 역할 가져오기
            role_name = "인증 유저"
            try:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    logging.debug(f"{role_name}: {bool(role)}")
                else:
                    logging.error(f"역할 '{role_name}'을 찾을 수 없습니다. 역할이 존재하는지 확인해주세요.")
                    raise ValueError(f"역할 '{role_name}'을 찾을 수 없습니다.")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"역할을 가져오는 중 오류 발생: {tb}")
                return

            # 역할 부여
            try:
                await payload.member.add_roles(role)
                logging.debug(f"{user}에게 인증 유저 역할을 성공적으로 부여했습니다.")
            except discord.Forbidden:
                logging.error(f"{user}에게 역할을 부여할 수 없습니다. 권한을 확인해주세요.")
                return
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"역할 부여 중 오류 발생: {tb}")
                return

            # 입장 로그
            if role_name in user_roles:
                logging.debug(f"{user}가 이미 '{role_name}' 역할을 가지고 있습니다. 입장 로그를 보내지 않습니다.")
            else:
                try:
                    cursor.execute(f"SELECT inviter_id FROM users WHERE discord_user_id = {payload.user_id};")
                    result = cursor.fetchone()
                    logging.debug(f"result: {result}")
                    inviter = guild.get_member(result[0])
                    cursor.execute(f"SELECT invite_count FROM users WHERE discord_user_id = {result[0]};")
                    result = cursor.fetchone()
                    invite_count = result[0]
                    logging.debug(f"{user}의 초대자 정보: {inviter.display_name}, 초대 횟수: {invite_count}")
                except Exception as e:
                    tb = traceback.format_exc()
                    logging.error(f"DB에서 초대자 정보를 가져오는 중 오류 발생: {tb}")

                try:
                    await entry_log_channel.send(
                        f"{payload.member.display_name}님, 𝔥𝔢𝔞𝔳𝔢𝔫'𝔰 𝔡𝔯𝔞𝔤𝔬𝔫에 입성하신것을 환영합니다!\n"
                        f"{payload.member.mention}님은 {inviter.mention}님이 초대하신 {invite_count}번째 유저입니다.\n")
                    logging.debug(f"{user}님의 입장로그를 성공적으로 보냈습니다.")
                except discord.Forbidden:
                    logging.error(f"{user}에게 메시지를 보낼 수 없습니다. 권한을 확인해주세요.")
                except Exception as e:
                    tb = traceback.format_exc()
                    logging.error(f"메시지를 보내는 중 오류 발생: {tb}")

            logging.info(f"{user}가 서버에 입장했습니다. 역할 부여 및 입장 로그를 성공적으로 완료했습니다.")
        elif payload.message_id == shared["event_message_id"]:
            logging.debug(f"{user}가 이벤트 메시지에 반응했습니다.")

            # 역할 가져오기
            role_name = "이벤트 참여자"
            role = None
            try:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    logging.debug(f"{role_name}: {bool(role)}")
                else:
                    logging.error(f"역할 '{role_name}'을 찾을 수 없습니다. 역할이 존재하는지 확인해주세요.")
                    raise ValueError(f"역할 '{role_name}'을 찾을 수 없습니다.")
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"역할을 가져오는 중 오류 발생: {tb}")
                return

            # 역할 부여
            try:
                await payload.member.add_roles(role)
                logging.debug(f"{user}에게 이벤트 참여자 역할을 성공적으로 부여했습니다.")
            except discord.Forbidden:
                logging.error(f"{user}에게 역할을 부여할 수 없습니다. 권한을 확인해주세요.")
                return
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"역할 부여 중 오류 발생: {tb}")
                return

            logging.info(f"{user}가 이벤트 참여자 역할을 부여받았습니다.")
        else:
            logging.debug(f"{user}(이)가 다른 메시지에 반응했습니다.")
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logging.debug("on_member_join실행됨")

        shared = self.bot.shared_data
        guild = self.bot.get_guild(shared["GUILD_ID"])
        channel_id = shared["PEOPLE_COUNT_CHANNEL_ID"]
        user = f"{member.display_name}[{member.id}]"
        db = shared["DB"]
        discord_user = await self.bot.fetch_user(member.id)

        # 음성 채널 가져오기
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                logging.error(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
                raise ValueError(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
            logging.debug(f"음성 채널: {bool(channel)}")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"음성 채널을 가져오는 중 오류 발생: {tb}")
            return

        # 음성 채널 이름 변경
        try:
            new_name = f"현재 인원: {guild.member_count}명 📡"
            await channel.edit(name=new_name)
            logging.info(f"음성 채널 이름을 '{new_name}'으로 성공적으로 변경했습니다.")
        except discord.Forbidden:
            logging.error("음성 채널 이름을 변경할 권한이 없습니다. 권한을 확인해주세요.")
            return
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"음성 채널 이름 변경 중 오류 발생: {tb}")
            return

        logging.info(f"{user} - 서버 입장.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        logging.debug("on_member_remove실행됨")

        shared = self.bot.shared_data
        guild = self.bot.get_guild(shared["GUILD_ID"])
        channel_id = shared["PEOPLE_COUNT_CHANNEL_ID"]
        user = f"{member.display_name}[{member.id}]"
        db = shared["DB"]

        # 음성 채널 가져오기
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                logging.error(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
                raise ValueError(f"채널 ID {channel_id}에 해당하는 음성 채널을 찾을 수 없습니다.")
            logging.debug(f"음성 채널: {bool(channel)}")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"음성 채널을 가져오는 중 오류 발생: {tb}")
            return

        # 음성 채널 이름 변경
        try:
            new_name = f"현재 인원: {guild.member_count}명 📡"
            await channel.edit(name=new_name)
            logging.info(f"음성 채널 이름을 '{new_name}'으로 성공적으로 변경했습니다.")
        except discord.Forbidden:
            logging.error("음성 채널 이름을 변경할 권한이 없습니다. 권한을 확인해주세요.")
            return
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"음성 채널 이름 변경 중 오류 발생: {tb}")
            return

        # DB에 사용자 정보 삭제
        cursor = shared["CURSOR"]
        try:
            # 사용자 정보 제거
            cursor.execute(f"DELETE FROM users WHERE discord_user_id = {member.id};")
            db.commit()
            logging.debug(f"{user}의 정보를 DB에 성공적으로 삭제했습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"DB에 사용자 정보를 삭제하는 중 오류 발생: {tb}")
            return
        logging.info(f"{user} - 서버 퇴장.")

    @commands.Cog.listener()
    async def on_message(self, message):
        logging.debug("on_message실행됨")

        shared = self.bot.shared_data
        user = f"{message.author.display_name}[{message.author.id}]"
        cursor = shared["CURSOR"]
        log_channel_id = self.bot.get_channel(shared["INVITE_LOG_CHANNEL_ID"])
        db = shared["DB"]

        # 봇 자신의 메시지는 무시
        if message.author == self.bot.user:
            return

        if message.channel.id in [1389249659184349396, 1389174108213743636, 1384506206596632626, 1388846281723609168]:
            logging.debug("메시지가 기록되지 않는 채널에서 수신되었습니다.")
        else:
            if message.content == "":
                logging.debug(f"메시지 수신: 첨부파일 - {user} ({message.channel.name})")
            else:
                logging.debug(f"메시지 수신: \"{message.content}\" - {user} ({message.channel.name})")

        # 초대 정보 저장
        try:
            if "unknownInviter" in message.content:
                logging.debug("초대 정보가 없습니다.")
                await log_channel_id.send(f"초대 정보가 없습니다.\n"
                                          "관리자뷰를 통해 수동으로 초대 정보를 저장해주세요. `/초대정보-추가`")
                return
            elif message.channel.id == 1390313743564406785 and message.author.id == 499595256270946326:
                inviter_id : int = message.content.split("/")[1] # 얘 unknownInviter일 때 그거 해야함
                invited_member_id : int = message.content.split("/")[2]
                logging.debug(f"inviter\"{inviter_id}\" invited\"{invited_member_id}\"")

                try:
                    # 사용자 중복 확인
                    cursor.execute(f"SELECT COUNT(*) FROM users WHERE discord_user_id = {invited_member_id}")
                    exists = cursor.fetchone()[0]
                    if exists:
                        logging.debug(f"{user}는 이미 DB에 존재합니다.")
                        await log_channel_id.send(f"초대된 사용자가 이미 DB에 존재합니다.")
                        return

                    # 사용자 정보 삽입
                    cursor.execute(f"INSERT INTO users (discord_user_id, inviter_id) VALUES ({invited_member_id}, {inviter_id})")
                    db.commit()
                    logging.debug(f"{user}의 정보를 DB에 성공적으로 저장했습니다.")
                except Exception as e:
                    tb = traceback.format_exc()
                    logging.error(f"DB에 사용자 정보를 저장하는 중 오류 발생: {tb}")
                    return

                cursor.execute(f"SELECT * FROM users WHERE discord_user_id = {invited_member_id};")
                result = cursor.fetchone()

                invited_member = await self.bot.fetch_user(invited_member_id)
                logging.debug(f"invited_member::: {invited_member}")

                # on_message이벤트 리스너가 on_member_join이벤트 리스너보다 먼저 실행된 경우
                if result == None:
                    logging.warning(f"초대된 사용자가 DB에 존재하지 않습니다: {invited_member_id}")
                    await log_channel_id.send(f"초대된 사용자가 DB에 존재하지 않습니다: {invited_member.mention}\n"
                                              "관리자뷰를 통해 수동으로 초대 정보를 저장해주세요. `/초대정보-추가`")
                    return

                cursor.execute(f"UPDATE users SET invite_count = invite_count + 1 WHERE discord_user_id = {inviter_id};")
                cursor.execute(f"UPDATE users SET experience = experience + 100 WHERE discord_user_id = {inviter_id};")
                db.commit()

                logging.debug("초대 정보가 성공적으로 저장되었습니다.")
                return
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"초대 정보 저장 중 오류 발생: {tb}")
            return

        # 경험치 부여
        try:
            # 사용자 정보 업데이트
            cursor.execute(f"UPDATE users SET experience = experience + 1 WHERE discord_user_id = {message.author.id};")
            db.commit()
            logging.debug(f"{user}에게 1 경험치를 부여했습니다.")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"on_message의 경험치 부여 중 오류 발생: {tb}")
            return


async def setup(bot):
    await bot.add_cog(Events(bot))
    logging.debug("Events cog이 성공적으로 로드되었습니다.")
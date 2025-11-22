from telebot.async_telebot import AsyncTeleBot

from shared.config import settings
from shared.database.models import CameFrom

class CameFromService:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.channels = {
            CameFrom.MARA: settings.telegram.mara_channel,
            CameFrom.DASHA: settings.telegram.mara_channel,
        }

    async def check_user(self, user_id: int):
        is_mara = False
        is_dasha = False
        for owner, channel in self.channels.items():
            if await self._check_user_in_channel(user_id, channel):
                if owner == CameFrom.MARA:
                    is_mara = True
                elif owner == CameFrom.DASHA:
                    is_dasha = True

        if is_mara and is_dasha:
            return CameFrom.BOTH
        elif is_mara:
            return CameFrom.MARA
        elif is_dasha:
            return CameFrom.DASHA
        else:
            return CameFrom.GUEST


    async def _check_user_in_channel(self, user_id: int, channel: str) -> bool:
        try:
            user = await self.bot.get_chat_member(channel, user_id)
        except Exception:
            return False
        else:
            return bool(user)

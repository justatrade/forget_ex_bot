from typing import TypeVar, Protocol

from pydantic import BaseModel

from shared.config import settings


class SpecialPresenceProtocol(Protocol):
    ny_special: bool | None
    feb_special: bool | None
    twelve_special: bool | None


class SpecialPresenceMixin:
    T = TypeVar("T", bound=SpecialPresenceProtocol)

    @property
    def all_special(self: T) -> bool:
        return bool(
            self.ny_special and
            self.feb_special and
            self.twelve_special
        )

    @property
    def any_special(self: T) -> bool:
        return bool(
            self.ny_special or
            self.feb_special or
            self.twelve_special
        )


class DashaChannelPresence(BaseModel, SpecialPresenceMixin):
    ny_special: bool = False
    feb_special: bool = False
    twelve_special: bool = False


class DashaMaraChannelPresence(BaseModel):
    dasha: bool = False
    mara: bool = False


CHANNEL_ID_TO_FIELD_MAP: dict[int, str] = {
    settings.special.channel_ny: "ny_special",
    settings.special.channel_feb: "feb_special",
    settings.special.channel_12: "twelve_special",
    settings.telegram.dasha_channel: "dasha",
    settings.telegram.mara_channel: "mara",
}

CHANNEL_FIELD_TO_ID_MAP: dict[str, int] = {
    v: k for k, v
    in CHANNEL_ID_TO_FIELD_MAP.items()
}
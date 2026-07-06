"""Персистентное FSM-хранилище aiogram поверх основной SQLite-базы бота.

Заменяет MemoryStorage, чтобы незавершённые сценарии (оформление заказа,
админ-флоу) не терялись при рестарте бота.
"""
import json
from typing import Any, Dict, Mapping, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder, StateType, StorageKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import FSMData


class SQLiteFSMStorage(BaseStorage):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.key_builder = DefaultKeyBuilder(with_bot_id=True, with_destiny=True)

    def _key(self, key: StorageKey) -> str:
        return self.key_builder.build(key)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if isinstance(state, State) else state
        async with self.session_factory() as session:
            row = await session.get(FSMData, self._key(key))
            if row is None:
                if value is None:
                    return
                session.add(FSMData(key=self._key(key), state=value))
            else:
                row.state = value
            await session.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self.session_factory() as session:
            row = await session.get(FSMData, self._key(key))
            return row.state if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        value = json.dumps(dict(data), ensure_ascii=False, default=str) if data else None
        async with self.session_factory() as session:
            row = await session.get(FSMData, self._key(key))
            if row is None:
                if value is None:
                    return
                session.add(FSMData(key=self._key(key), data=value))
            else:
                row.data = value
            await session.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with self.session_factory() as session:
            row = await session.get(FSMData, self._key(key))
            if row is None or not row.data:
                return {}
            return json.loads(row.data)

    async def close(self) -> None:
        # Соединения закрывает Database.close() через dispose() движка
        pass

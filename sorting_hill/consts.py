"""Модуль с константами"""

from enum import StrEnum


class EventType(StrEnum):
    ShiftStarted = 'начало работ'
    ShiftEnded = 'окончание работ'
    WagonArrived = 'вагон на сортировку'
    LocoArrived = 'подача локомотива'
    TrainPlanned = 'формируйте состав'
    TrainReady = 'отправляйте поезд'
    PreparePath = 'готовьте путь'


class TrainType(StrEnum):
    Gruz = 'Г'
    Pass = 'Л'
    OpasnGruz = 'О'


class WagonType(StrEnum):
    Empty = 'П'
    Gruz = 'Г'
    Pass = 'Л'
    OpasnGruz = 'О'


class LocoType(StrEnum):
    Electro16 = 'ЭВЛ-16'
    Electro32 = 'ЭВЛ-32'
    Diesel24 = 'ДЛ-24'
    Diesel64 = 'ТДЛ-64'


EVENTS_BALANCED = [
    EventType.WagonArrived, EventType.WagonArrived, EventType.WagonArrived, EventType.WagonArrived,
    EventType.WagonArrived, EventType.WagonArrived, EventType.WagonArrived, EventType.WagonArrived,
    EventType.WagonArrived, EventType.LocoArrived, EventType.LocoArrived, EventType.LocoArrived,
    EventType.LocoArrived, EventType.PreparePath, EventType.PreparePath, EventType.TrainPlanned, EventType.TrainReady
]

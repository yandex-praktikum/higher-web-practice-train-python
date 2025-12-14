"""
План тестирования (интеграционные/нефункциональные, static integrity):

- test_main_py_is_unchanged: исходник main.py не изменён.
- test_consts_py_is_unchanged: исходник sorting_hill/consts.py не изменён.
- test_sorting_hill_py_is_unchanged: исходник sorting_hill/sorting_hill.py не изменён.

"""

import ast
import os
import pathlib
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------- эталоны исходников (жёстко зашиты) ----------

_ETALON_MAIN = r'''"""Главный модуль проекта"""

import random
import time

from sorting_handler.sorting_operator import SortingOperatorImpl
from sorting_handler.sorting_reporter import SortingReporterImpl
from sorting_hill.consts import EVENTS_BALANCED, EventType, WagonType
from sorting_hill.sorting_hill import SortingHill


def main() -> None:
    """Точка входа"""

    number_of_paths = max(2, random.randint(0, 15))
    sorting_hill = SortingHill(number_of_paths)

    try:
        sorting_hill.register_handler(SortingOperatorImpl)
        sorting_hill.register_handler(SortingReporterImpl)
    except Exception:
        print('Нет зарегистрированных операторов, работы не выполняются.')

    wagon_left = max(1024, random.randint(1024, 4095))
    for _ in range(wagon_left):
        wagon_num = random.randint(0, 99999999)
        wagon_type = random.choice(list(WagonType))
        sorting_hill.wagon_buffer.append(f'{wagon_num:08d}/{wagon_type}')

    print(f'Начало рабочей смены, очередь вагонов: {wagon_left}')
    sorting_hill.handle_event(EventType.ShiftStarted)

    while sorting_hill.wagon_buffer:
        try:
            next_event = random.choice(EVENTS_BALANCED)
            if sorting_hill.check_event(next_event) is not None:
                print(f'Команда дежурного: {next_event}')
                sorting_hill.handle_event(next_event)
                time.sleep(random.uniform(0, 0.1))
        except RuntimeError as e:
            print(f'Произошла ошибка обработки: {e}')

    sorting_hill.handle_event(EventType.ShiftEnded)
    print('Рабочая смена окончена')

if __name__ == '__main__':
    main()
'''

_ETALON_CONSTS = r'''"""Модуль с константами"""

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
'''

_ETALON_SORTING_HILL = r'''import random

from sorting_handler.interface import SortingHandler
from sorting_hill.consts import EventType, LocoType

class SortingHill:
    """Класс для запуска сервиса"""

    def __init__(self, number_of_paths: int):
        """Инициализация сервиса"""

        self.handlers: list[SortingHandler] = []
        self._number_of_paths = number_of_paths
        self.assigned_paths: dict[int, str | None] = {}
        self.wagon_buffer: list[str] = []
        self.trains_formed: dict[str, list[str]] = {}
        self.train_index = 0

    def get_number_of_paths(self) -> int:
        """
        Геттер для получения количества путей

        :return: Количество путей
        """
        return self._number_of_paths

    def handle_event(self, event: EventType) -> None:
        """
        Обработчик событий.

        :param event: Тип события (один из членов строкового енама)
        :raises RuntimeError: Если передано неизвестное событие.
        """

        exc = None
        try:
            match event:
                case EventType.ShiftStarted:
                    for handler in self.handlers:
                        handler.start_shift()

                case EventType.ShiftEnded:
                    last_trains_count = 0
                    for path in self.assigned_paths.copy():
                        train = self.assigned_paths.get(path)
                        train_content = self.trains_formed.get(train, [])
                        if train_content and len(train_content) > 1:
                            last_trains_count += 1
                        else:
                            if train in self.trains_formed:
                                del self.trains_formed[train]
                            del self.assigned_paths[path]

                    while last_trains_count > 0:
                        self.handle_event(EventType.TrainReady)
                        last_trains_count -= 1

                    for handler in self.handlers:
                        handler.end_shift()

                case EventType.PreparePath:
                    for handler in self.handlers:
                        handler.prepare_path()

                case EventType.WagonArrived:
                    if not self.wagon_buffer:
                        return

                    wagon_info = self.wagon_buffer[0]

                    for handler in self.handlers:
                        handler.handle_wagon(wagon_info)
                    self.wagon_buffer.pop(0)

                case EventType.LocoArrived:
                    loco = random.choice(list(LocoType))
                    for handler in self.handlers:
                        handler.handle_locomotive(loco)

                case EventType.TrainPlanned:
                    for handler in self.handlers:
                        handler.allocate_path_for_train()

                case EventType.TrainReady:
                    for handler in self.handlers:
                        handler.send_train()

                case _:
                    raise RuntimeError(f'unknown event: {event}')
        except RuntimeError as e:
            exc = e

        if exc:
            raise exc

    def check_event(self, candidate: EventType) -> str | None:
        """
        Проверка события.

        :param candidate: Событие-кандидат для проверки.
        :return: Строка с событием, если оно прошло проверку, либо None.
        """
        match candidate:
            case EventType.PreparePath:
                if len(self.assigned_paths) >= self._number_of_paths:
                    return None
            case EventType.LocoArrived:
                if not any(content == [] for content in self.trains_formed.values()):
                    return None
            case EventType.TrainPlanned:
                if not any(train is None for train in self.assigned_paths.values()):
                    return None
            case EventType.TrainReady:
                ready_train = None
                for train, train_content in self.trains_formed.items():
                    if not train_content:
                        continue

                    maybe_loco = train_content[0]
                    if maybe_loco not in LocoType:
                        break

                    loco_descr = maybe_loco.split('-')
                    train_size = int(loco_descr[-1])

                    if len(train_content) == train_size + 1 or (len(train_content) > 1 and not self.wagon_buffer):
                        ready_train = train
                        break

                if not ready_train:
                    return None
            case _:
                return candidate

        return candidate

    def register_handler(self, handler: type[SortingHandler]) -> None:
        """
        Зарегистрировать обработчик.

        :param handler: Обработчик для регистрации.
        """
        self.handlers.append(handler(self))
'''


# ---------- утилиты ----------

def _normalize_python(source_text: str, path: pathlib.Path) -> str:
    """Мини-нормализация: AST parse→unparse для устойчивости к форматированию."""
    try:
        node = ast.parse(source_text)
    except SyntaxError as error:
        raise AssertionError(
            f'Убедитесь, что файл сохраняет корректный синтаксис Python: разбор AST завершился ошибкой в файле {path.as_posix()}.'
        ) from error
    try:
        return ast.unparse(node)
    except Exception as error:  # noqa: BLE001
        raise AssertionError(
            f'Проверьте, что файл корректно разворачивается из AST (ast.unparse) в файле {path.as_posix()}.'
        ) from error


def _read_text(path: pathlib.Path) -> str:
    """Чтение текста из файла."""
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError as error:
        raise AssertionError(
            f'Убедитесь, что файл существует: {path.as_posix()}'
        ) from error


# ---------- тесты ----------

def test_main_py_is_unchanged() -> None:
    project_main_path = pathlib.Path('main.py')
    actual = _normalize_python(_read_text(project_main_path), project_main_path)
    etalon = _normalize_python(_ETALON_MAIN, project_main_path)
    assert actual == etalon, (
        'Убедитесь, что main.py не изменён относительно прекода (шаблона проекта). '
        f'Ожидалось точное совпадение текста, получено различие в файле: {project_main_path.as_posix()}'
    )


def test_consts_py_is_unchanged() -> None:
    consts_path = pathlib.Path('sorting_hill') / 'consts.py'
    actual = _normalize_python(_read_text(consts_path), consts_path)
    etalon = _normalize_python(_ETALON_CONSTS, consts_path)
    assert actual == etalon, (
        'Убедитесь, что sorting_hill/consts.py не изменён относительно прекода (шаблона проекта). '
        f'Ожидалось точное совпадение текста, получено различие в файле: {consts_path.as_posix()}'
    )


def test_sorting_hill_py_is_unchanged() -> None:
    hill_path = pathlib.Path('sorting_hill') / 'sorting_hill.py'
    actual = _normalize_python(_read_text(hill_path), hill_path)
    etalon = _normalize_python(_ETALON_SORTING_HILL, hill_path)
    assert actual == etalon, (
        'Убедитесь, что sorting_hill/sorting_hill.py не изменён относительно прекода (шаблона проекта). '
        'Ожидалось точное совпадение текста, получено различие.'
    )

import random

from sorting_handler.interface import SortingHandler
from sorting_hill.consts import EventType, LocoType, TrainType, WagonType

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

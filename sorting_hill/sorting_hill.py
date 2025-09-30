import random

from sorting_handler.interface import SortingHandler
from sorting_hill.consts import EventType, LocoType, TrainType, WagonType


class HiddenException(Exception):
    pass

class HiddenWatchImpl(SortingHandler):
    def __init__(self, sorting_hill: 'SortingHill'):
        self.sorting_hill = sorting_hill

    def handle_wagon(self, wagon_info: str) -> str:
        if not self.sorting_hill.assigned_paths:
            raise HiddenException('no path')

        wagon_descr = wagon_info.split('/')
        wagon_type = wagon_descr[-1]
        train_candidate = None
        train_path = None

        for path, train in self.sorting_hill.assigned_paths.items():
            if not train:
                continue

            train_type = train[-1] if train else None
            train_content = self.sorting_hill.trains_formed.get(train, [])

            if train_content:
                loco_info = train_content[0]
                loco_descr = loco_info.split('-')
                loco_max_wagons = int(loco_descr[-1])

                if loco_max_wagons > len(train_content) - 1:
                    if train_type in [WagonType.Gruz, WagonType.OpasnGruz]:
                        if wagon_type == train_type or wagon_type == WagonType.Empty:
                            train_candidate = train
                    elif train_type == WagonType.Pass:
                        if wagon_type == train_type:
                            train_candidate = train
                    else:
                        if wagon_type != WagonType.Pass or len(train_content) == 1:
                            train_candidate = train

            if train_candidate:
                train_path = path
                break

        if train_candidate is None:
            raise HiddenException('no free train')

        train_type = None
        for t in TrainType:
            if train_candidate.endswith(t):
                train_type = t

        if train_type is None and wagon_type != WagonType.Empty:
            train_type = wagon_type
            typed_train_candidate = train_candidate + train_type
            self.sorting_hill.trains_formed[typed_train_candidate] = self.sorting_hill.trains_formed.pop(train_candidate)
            self.sorting_hill.assigned_paths[train_path] = typed_train_candidate
            train_candidate = typed_train_candidate
            print(f'тип поезда определён {typed_train_candidate}')

        self.sorting_hill.trains_formed[train_candidate].append(wagon_info)
        return train_candidate

    def handle_locomotive(self, locomotive: str) -> str:
        for train, content in self.sorting_hill.trains_formed.items():
            if not content:
                content.append(locomotive)
                return train
        raise HiddenException('no train to add loco')

    def prepare_path(self) -> int:
        for p in range(1, self.sorting_hill._number_of_paths + 1):
            if p not in self.sorting_hill.assigned_paths:
                self.sorting_hill.assigned_paths[p] = None
                return p
        raise HiddenException('no free path')

    def allocate_path_for_train(self) -> dict[int, str]:
        for path, train in self.sorting_hill.assigned_paths.items():
            if train is None:
                next_train = f'{self.sorting_hill.train_index + 1:04d}'
                self.sorting_hill.train_index += 1
                self.sorting_hill.assigned_paths[path] = next_train
                self.sorting_hill.trains_formed[next_train] = []
                return {path: next_train}
        raise HiddenException('no path for train')

    def send_train(self) -> str:
        for path, train in self.sorting_hill.assigned_paths.items():
            if train is None:
                continue

            train_content = self.sorting_hill.trains_formed.get(train, [])
            if not train_content:
                continue

            maybe_loco = train_content[0]
            if maybe_loco not in LocoType:
                raise HiddenException(f'no loco found for train {train}')

            loco_descr = maybe_loco.split('-')
            train_size = int(loco_descr[-1])

            if len(train_content) == train_size + 1 or (len(train_content) > 1 and not self.sorting_hill.wagon_buffer):
                print(f'поезд {train} отправляется с пути {path}')
                del self.sorting_hill.trains_formed[train]
                del self.sorting_hill.assigned_paths[path]
                return train

        raise HiddenException('no ready train')

    def start_shift(self) -> None:
        pass

    def end_shift(self) -> None:
        pass


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
        self.hidden_watch_handler: HiddenWatchImpl | None = None

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

        watcher_exception = None
        try:
            match event:
                case EventType.ShiftStarted:
                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.start_shift()
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

                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.end_shift()
                    for handler in self.handlers:
                        handler.end_shift()

                case EventType.PreparePath:
                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.prepare_path()
                    for handler in self.handlers:
                        handler.prepare_path()

                case EventType.WagonArrived:
                    if not self.wagon_buffer:
                        return

                    wagon_info = self.wagon_buffer[0]

                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.handle_wagon(wagon_info)
                        self.wagon_buffer.pop(0)
                    for handler in self.handlers:
                        handler.handle_wagon(wagon_info)

                case EventType.LocoArrived:
                    loco = random.choice(list(LocoType))
                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.handle_locomotive(loco)
                    for handler in self.handlers:
                        handler.handle_locomotive(loco)

                case EventType.TrainPlanned:
                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.allocate_path_for_train()
                    for handler in self.handlers:
                        handler.allocate_path_for_train()

                case EventType.TrainReady:
                    if self.hidden_watch_handler:
                        self.hidden_watch_handler.send_train()
                    for handler in self.handlers:
                        handler.send_train()

                case _:
                    raise RuntimeError(f'unknown event: {event}')
        except HiddenException as he:
            watcher_exception = he

        if watcher_exception:
            raise watcher_exception

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

"""Главный модуль проекта"""

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

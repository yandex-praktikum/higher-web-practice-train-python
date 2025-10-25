"""
План тестирования (юниты для SortingReporterImpl)
=================================================
Позитивные тесты:
- test_start_shift_resets_stats:
  метод start_shift сбрасывает статистику и инициализирует базовый снэпшот.
- test_prepare_and_allocate_update_counters:
  методы prepare_path/allocate_path_for_train фиксируют рост путей и поездов.
- test_handle_locomotive_increments_counter:
  метод handle_locomotive увеличивает счётчик прибывших локомотивов.
- test_handle_wagon_counts_via_total_wagons_growth:
  метод handle_wagon учитывает обработанный вагон по изменению total_wagons.
- test_send_train_increments_trains_sent:
  метод send_train отражает убыль поездов в trains_formed как отправку.

Замечания:
- Репортёр не изменяет состояние напрямую, а сравнивает снэпшоты SortingHill.
"""
import os
import sys
from typing import Tuple
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sorting_hill.sorting_hill import SortingHill
from sorting_hill.consts import WagonType, LocoType
from sorting_handler.sorting_operator import SortingOperatorImpl
from sorting_handler.sorting_reporter import SortingReporterImpl


# ---------- фикстуры ----------

@pytest.fixture
def hill() -> SortingHill:
    """Короткая фабрика сортировочной горки."""
    return SortingHill(number_of_paths=3)


@pytest.fixture
def operator(hill: SortingHill) -> SortingOperatorImpl:
    """Оператор выполняет изменения состояния до репортёра."""
    return SortingOperatorImpl(hill)


@pytest.fixture
def reporter(hill: SortingHill) -> SortingReporterImpl:
    """Репортёр фиксирует изменения состояния."""
    rep = SortingReporterImpl(hill)
    rep.start_shift()
    return rep


# ---------- вспомогалка ----------

def _plan_train(operator: SortingOperatorImpl, reporter: SortingReporterImpl) -> Tuple[int, str]:
    """Готовим путь и планируем поезд, синхронно обновляя репортёр."""
    prepared_path = operator.prepare_path()
    reporter.prepare_path()

    allocation = operator.allocate_path_for_train()
    reporter.allocate_path_for_train()

    (path_number, train_number) = next(iter(allocation.items()))
    assert path_number == prepared_path, (
        'Убедитесь, что поезд размещается на только что подготовленном пути: '
        'метод allocate_path_for_train возвращает путь, совпадающий с результатом prepare_path.'
    )
    assert train_number in reporter.sorting_hill.trains_formed, (
        'Проверьте, что после allocate_path_for_train идентификатор поезда присутствует в trains_formed.'
    )
    return path_number, train_number


# ---------- позитивные юниты ----------

def test_start_shift_resets_stats(reporter: SortingReporterImpl) -> None:
    """start_shift: сбрасывает статистику и готовит снэпшот."""
    for key in ('paths_prepared', 'trains_planned', 'locos_arrived', 'wagons_handled', 'trains_sent'):
        assert reporter.stats[key] == 0, (
            'Убедитесь, что метод start_shift инициализирует счётчик '
            f'"{key}" нулём перед началом фиксации событий.'
        )


def test_prepare_and_allocate_update_counters(operator: SortingOperatorImpl, reporter: SortingReporterImpl) -> None:
    """prepare_path/allocate_path_for_train: отражают рост путей и поездов в статистике."""
    _plan_train(operator, reporter)

    assert reporter.stats['paths_prepared'] >= 1, (
        'Проверьте, что метод prepare_path в связке с репортёром увеличивает '
        'счётчик "paths_prepared" как минимум на 1.'
    )
    assert reporter.stats['trains_planned'] >= 1, (
        'Убедитесь, что метод allocate_path_for_train фиксируется репортёром и увеличивает '
        'счётчик "trains_planned" минимум на 1.'
    )


def test_handle_locomotive_increments_counter(operator: SortingOperatorImpl, reporter: SortingReporterImpl) -> None:
    """handle_locomotive: увеличивает счётчик прибывших локомотивов."""
    _plan_train(operator, reporter)

    operator.handle_locomotive(LocoType.Electro32)
    reporter.handle_locomotive(LocoType.Electro32)

    assert reporter.stats['locos_arrived'] >= 1, (
        'Проверьте, что метод handle_locomotive в репортёре учитывает прибытие и '
        'увеличивает "locos_arrived" хотя бы на 1.'
    )


def test_handle_wagon_counts_via_total_wagons_growth(operator: SortingOperatorImpl, reporter: SortingReporterImpl) -> None:
    """handle_wagon: учитывает обработанный вагон по росту общего числа элементов состава."""
    _plan_train(operator, reporter)
    operator.handle_locomotive(LocoType.Electro16)
    reporter.handle_locomotive(LocoType.Electro16)

    wagon_info = f'10101010/{WagonType.Gruz}'
    operator.handle_wagon(wagon_info)
    reporter.handle_wagon(wagon_info)

    assert reporter.stats['wagons_handled'] >= 1, (
        'Убедитесь, что метод handle_wagon фиксирует обработку вагона: '
        'счётчик "wagons_handled" увеличивается минимум на 1 после добавления вагона в состав.'
    )


def test_send_train_increments_trains_sent(operator: SortingOperatorImpl, reporter: SortingReporterImpl, hill: SortingHill) -> None:
    """send_train: отражает отправку поезда по убыли trains_formed."""
    _plan_train(operator, reporter)
    operator.handle_locomotive(LocoType.Diesel24)
    reporter.handle_locomotive(LocoType.Diesel24)

    operator.handle_wagon(f'22222222/{WagonType.Gruz}')
    reporter.handle_wagon(f'22222222/{WagonType.Gruz}')
    operator.handle_wagon(f'33333333/{WagonType.Gruz}')
    reporter.handle_wagon(f'33333333/{WagonType.Gruz}')

    operator.send_train()
    reporter.send_train()

    assert reporter.stats['trains_sent'] >= 1, (
        'Проверьте, что метод send_train в репортёре фиксирует отправку поезда: '
        'счётчик "trains_sent" становится не меньше 1 после удаления состава из trains_formed.'
    )

"""
План тестирования (юниты для SortingOperatorImpl)
=================================================
Позитивные тесты:
- test_prepare_path_allocates_free_path:
  метод prepare_path подготавливает первый свободный путь и регистрирует его.
- test_allocate_path_creates_empty_train:
  метод allocate_path_for_train размещает поезд на подготовленном пути и создаёт пустой состав.
- test_handle_locomotive_puts_into_empty_train:
  метод handle_locomotive прикрепляет локомотив к первому пустому составу.
- test_handle_wagon_deduces_type_and_renames_train:
  метод handle_wagon определяет тип состава по первому вагону и переименовывает идентификатор поезда.
- test_send_train_when_full_or_allowed:
  метод send_train отправляет готовый поезд и освобождает путь.

Негативные тесты:
- test_handle_wagon_without_paths_raises:
  метод handle_wagon вызывается до подготовки путей — ожидается исключение.
- test_second_allocate_without_free_path_raises:
  метод allocate_path_for_train вызывается повторно без свободного места — ожидается исключение.
"""

import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sorting_hill.sorting_hill import SortingHill
from sorting_hill.consts import WagonType, LocoType
from sorting_handler.sorting_operator import SortingOperatorImpl


# ---------- фикстуры ----------

@pytest.fixture
def hill() -> SortingHill:
    """Короткая фабрика сортировочной горки."""
    return SortingHill(number_of_paths=2)


@pytest.fixture
def operator(hill: SortingHill) -> SortingOperatorImpl:
    """Экземпляр оператора для юнит-тестов."""
    return SortingOperatorImpl(hill)


# ---------- позитивные юниты ----------

def test_prepare_path_allocates_free_path(operator: SortingOperatorImpl, hill: SortingHill) -> None:
    """prepare_path: подготавливает путь и регистрирует его в assigned_paths."""
    prepared_path = operator.prepare_path()
    assert prepared_path == 1, (
        'Убедитесь, что метод prepare_path подготавливает первый свободный путь и возвращает номер 1.'
    )
    assert prepared_path in hill.assigned_paths, (
        'Проверьте, что метод prepare_path регистрирует подготовленный путь в SortingHill.assigned_paths.'
    )


def test_allocate_path_creates_empty_train(operator: SortingOperatorImpl, hill: SortingHill) -> None:
    """allocate_path_for_train: создаёт пустой состав и назначает номер поезда на подготовленном пути."""
    path_number = operator.prepare_path()
    allocation = operator.allocate_path_for_train()
    assert allocation == {path_number: '0001'}, (
        'Убедитесь, что метод allocate_path_for_train назначает поезду номер "0001" на только что подготовленном пути.'
    )
    assert hill.trains_formed['0001'] == [], (
        'Проверьте, что после allocate_path_for_train создаётся пустой состав (список элементов поезда пуст).'
    )
    assert hill.assigned_paths[path_number] == '0001', (
        'Убедитесь, что метод allocate_path_for_train связывает путь с номером поезда в assigned_paths.'
    )


def test_handle_locomotive_puts_into_empty_train(operator: SortingOperatorImpl, hill: SortingHill) -> None:
    """handle_locomotive: прикрепляет локомотив к первому пустому составу."""
    operator.prepare_path()
    operator.allocate_path_for_train()
    train_number = operator.handle_locomotive(LocoType.Electro16)
    assert train_number == '0001', (
        'Убедитесь, что метод handle_locomotive прикрепляет локомотив к поезду "0001" и возвращает его номер.'
    )
    assert hill.trains_formed['0001'] == [LocoType.Electro16], (
        'Проверьте, что после handle_locomotive первый элемент состава становится локомотивом (объект LocoType).'
    )


def test_handle_wagon_deduces_type_and_renames_train(operator: SortingOperatorImpl, hill: SortingHill) -> None:
    """handle_wagon: по первому вагону определяет тип состава и переименовывает идентификатор поезда."""
    path_number = operator.prepare_path()
    operator.allocate_path_for_train()
    locomotive = LocoType.Electro16
    operator.handle_locomotive(locomotive)

    wagon_info = f'12345678/{WagonType.Gruz}'
    new_train_id = operator.handle_wagon(wagon_info)

    assert new_train_id != '0001', (
        'Убедитесь, что метод handle_wagon переименовывает поезд, добавляя литеру типа (например, "0001Г"), '
        'а не оставляет идентификатор "0001" без типа.'
    )
    assert hill.assigned_paths[path_number] == new_train_id, (
        'Проверьте, что после handle_wagon путь начинает указывать на новый типизированный идентификатор поезда.'
    )
    assert new_train_id in hill.trains_formed and '0001' not in hill.trains_formed, (
        'Убедитесь, что метод handle_wagon переносит состав в словаре trains_formed на новый ключ '
        'и удаляет старый ключ "0001".'
    )
    assert hill.trains_formed[new_train_id] == [locomotive, wagon_info], (
        'Проверьте, что метод handle_wagon добавляет вагон в конец состава: сначала локомотив, затем новый вагон.'
    )


def test_send_train_when_full_or_allowed(operator: SortingOperatorImpl, hill: SortingHill) -> None:
    """send_train: отправляет готовый поезд и освобождает путь."""
    path_number = operator.prepare_path()
    operator.allocate_path_for_train()
    operator.handle_locomotive(LocoType.Diesel24)

    first_wagon = f'11111111/{WagonType.Gruz}'
    second_wagon = f'22222222/{WagonType.Gruz}'
    typed_train = operator.handle_wagon(first_wagon)
    _ = operator.handle_wagon(second_wagon)

    sent_train = operator.send_train()
    assert sent_train == typed_train, (
        'Убедитесь, что метод send_train отправляет именно сформированный поезд (идентификатор совпадает).'
    )
    assert sent_train not in hill.trains_formed, (
        'Проверьте, что метод send_train удаляет состав из SortingHill.trains_formed после отправки.'
    )
    assert path_number not in hill.assigned_paths, (
        'Убедитесь, что метод send_train освобождает путь: ключ пути удаляется из SortingHill.assigned_paths.'
    )


# ---------- негативные юниты ----------

def test_handle_wagon_without_paths_raises(operator: SortingOperatorImpl) -> None:
    """handle_wagon: вызов до подготовки путей приводит к ожидаемому исключению."""
    with pytest.raises(RuntimeError, match='no path'):
        operator.handle_wagon(f'99999999/{WagonType.Gruz}')


def test_second_allocate_without_free_path_raises(operator: SortingOperatorImpl) -> None:
    """allocate_path_for_train: повторный вызов без свободных слотов по пути приводит к ожидаемому исключению."""
    operator.prepare_path()
    operator.allocate_path_for_train()
    with pytest.raises(RuntimeError, match='no path for train'):
        operator.allocate_path_for_train()

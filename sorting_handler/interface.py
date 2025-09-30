import typing
from abc import ABC, abstractmethod

if typing.TYPE_CHECKING:
    from sorting_hill.sorting_hill import SortingHill


class SortingHandler(ABC):
    """Интерфейс хэндлера"""

    @abstractmethod
    def __init__(self, sorting_hill: 'SortingHill') -> None:
        """Инициализация хэндлера"""
        raise NotImplementedError

    @abstractmethod
    def handle_wagon(self, wagon_info: str) -> str:
        """
        Обработчик поступающих вагонов.

        :param wagon_info: Строка с информацией о вагоне в формате НОМЕР/Т(ип)
        :return: Номер поезда, в который попал вагон.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_locomotive(self, locomotive: str) -> str:
        """
        Обработчик поступающих локомотивов.

        :param locomotive: Модель локомотива в формате МОДЕЛЬ-ЧислоВагоновМакс
        :return: Номер поезда, в который попал локомотив.
        """
        raise NotImplementedError

    @abstractmethod
    def prepare_path(self) -> int:
        """
        Запрос на подготовку пути.

        :return: Подготовленный путь.
        """
        raise NotImplementedError

    @abstractmethod
    def allocate_path_for_train(self) -> dict[int, str]:
        """
        Запрос на размещение поезда на пути.

        :return: Словарь, в котором ключом выступает номер пути, а значением номер поезда.
        """
        raise NotImplementedError

    @abstractmethod
    def send_train(self) -> str:
        """
        Запрос на отправку готового поезда.

        :return: Номер отправленного поезда.
        """
        raise NotImplementedError

    @abstractmethod
    def start_shift(self) -> None:
        """Начало смены"""
        raise NotImplementedError

    @abstractmethod
    def end_shift(self) -> None:
        """Окончание смены"""
        raise NotImplementedError

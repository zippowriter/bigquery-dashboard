"""エンティティの基底クラス."""

from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel


IdType = TypeVar("IdType")


class Entity(BaseModel, Generic[IdType]):
    """DDDにおけるエンティティの基底クラス.

    エンティティは識別子によって同一性が定義される。
    同じ識別子を持つインスタンスは、他の属性が異なっていても等価とみなされる。
    """

    @property
    @abstractmethod
    def id(self) -> IdType:
        """エンティティの識別子を返す."""
        ...

    def __eq__(self, other: object) -> bool:
        """識別子に基づいて等価性を判定する."""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        """識別子に基づいて不等価性を判定する."""
        if not isinstance(other, self.__class__):
            return True
        return self.id != other.id

    def __hash__(self) -> int:
        """識別子に基づいてハッシュ値を計算する."""
        return hash(self.id)

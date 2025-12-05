from pydantic import BaseModel


class DeletionCandidate(BaseModel, frozen=True):
    """削除候補情報を表す値オブジェクト.

    不変であり、同じ値を持つインスタンスは等価として扱われる。
    """

    data_owner: str

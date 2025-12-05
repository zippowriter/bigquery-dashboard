from pydantic import BaseModel


class TableId(BaseModel, frozen=True):
    """BigQueryテーブルの識別子を表す値オブジェクト.

    不変であり、同じ値を持つインスタンスは等価として扱われる。
    """

    project_id: str
    dataset_id: str
    table_id: str

    @classmethod
    def from_fqn(cls, fqn: str) -> "TableId":
        """完全修飾名からTableIdを生成する.

        Args:
            fqn: "project_id.dataset_id.table_id" 形式の文字列

        Returns:
            TableId インスタンス

        Raises:
            ValueError: fqnの形式が不正な場合
        """
        parts = fqn.split(".")
        if len(parts) != 3:
            msg = f"Invalid FQN format: '{fqn}'. Expected 'project_id.dataset_id.table_id'"
            raise ValueError(msg)
        return cls(project_id=parts[0], dataset_id=parts[1], table_id=parts[2])

    @property
    def fqn(self) -> str:
        """完全修飾名を返す.

        Returns:
            "project_id.dataset_id.table_id" 形式の文字列
        """
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    def __str__(self) -> str:
        """文字列表現を返す."""
        return self.fqn

    def __repr__(self) -> str:
        """デバッグ用の詳細な文字列表現を返す."""
        return f"TableId({self.fqn})"

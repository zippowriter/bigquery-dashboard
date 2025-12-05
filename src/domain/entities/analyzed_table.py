from domain.entities.base import Entity
from domain.entities.table import Table
from domain.value_objects.deletion_candidate import DeletionCandidate
from domain.value_objects.table_id import TableId
from domain.value_objects.usage_info import UsageInfo


class AnalyzedTable(Entity[TableId]):
    """分析済みテーブルのモデル.

    Tableエンティティをコンポジションで保持し、
    ライフサイクル状態（利用状況、削除候補）を属性として管理する。

    状態遷移:
        Table(発見) → AnalyzedTable(usage_info設定) → AnalyzedTable(deletion_info設定)
    """

    table: Table
    usage_info: UsageInfo | None = None
    deletion_info: DeletionCandidate | None = None

    @property
    def id(self) -> TableId:
        """エンティティの識別子を返す."""
        return self.table.table_id

    @property
    def is_checked(self) -> bool:
        """参照回数がチェック済みかどうか."""
        return self.usage_info is not None

    @property
    def is_candidate(self) -> bool:
        """削除候補かどうか."""
        return self.deletion_info is not None

    def is_unused(self, threshold: int = 0) -> bool:
        """未使用テーブルかどうか.

        Raises:
            ValueError: 参照回数がチェックされていない場合
        """
        if self.usage_info is None:
            msg = "Usage info is not set. Call with_usage_info() first."
            raise ValueError(msg)
        return self.usage_info.is_unused(threshold)

    def with_usage_info(self, usage_info: UsageInfo) -> "AnalyzedTable":
        """利用状況を設定した新しいインスタンスを返す."""
        return AnalyzedTable(
            table=self.table,
            usage_info=usage_info,
            deletion_info=self.deletion_info,
        )

    def with_deletion_info(self, deletion_info: DeletionCandidate) -> "AnalyzedTable":
        """削除候補情報を設定した新しいインスタンスを返す."""
        return AnalyzedTable(
            table=self.table,
            usage_info=self.usage_info,
            deletion_info=deletion_info,
        )

    @classmethod
    def from_table(cls, table: Table) -> "AnalyzedTable":
        """Tableから新しいAnalyzedTableを生成する."""
        return cls(table=table)

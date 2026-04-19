from dataclasses import dataclass, field
from typing import List
from vaultpatch.compare import CompareResult
from vaultpatch.diff import SecretDiff


@dataclass
class ReportEntry:
    namespace: str
    path: str
    diffs: List[SecretDiff]

    @property
    def summary(self) -> str:
        added = sum(1 for d in self.diffs if d.is_added())
        removed = sum(1 for d in self.diffs if d.is_removed())
        changed = sum(1 for d in self.diffs if d.is_changed())
        parts = []
        if added:
            parts.append(f"+{added}")
        if removed:
            parts.append(f"-{removed}")
        if changed:
            parts.append(f"~{changed}")
        return " ".join(parts) if parts else "no changes"


@dataclass
class Report:
    entries: List[ReportEntry] = field(default_factory=list)

    def add(self, namespace: str, path: str, diffs: List[SecretDiff]) -> None:
        if diffs:
            self.entries.append(ReportEntry(namespace=namespace, path=path, diffs=diffs))

    @property
    def total_changes(self) -> int:
        return sum(len(e.diffs) for e in self.entries)

    @property
    def has_changes(self) -> bool:
        return len(self.entries) > 0

    def render(self) -> str:
        if not self.has_changes:
            return "No changes detected."
        lines = []
        for entry in self.entries:
            lines.append(f"[{entry.namespace}] {entry.path}  ({entry.summary})")
            for diff in entry.diffs:
                lines.append(f"  {diff.label()}  {diff.key}")
        lines.append(f"\nTotal changes: {self.total_changes}")
        return "\n".join(lines)


def build_report(compare_result: CompareResult) -> Report:
    report = Report()
    for namespace, path_diffs in compare_result.by_namespace.items():
        for path, diffs in path_diffs.items():
            report.add(namespace, path, diffs)
    return report

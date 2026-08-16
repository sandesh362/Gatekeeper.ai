"""Layer 1 — regex rules engine backed by rules.yaml."""

import re
from pathlib import Path

import yaml

from app.features.detection.schemas import RuleMatch

_RULES_PATH = Path(__file__).parent / "rules.yaml"


class RulesEngine:
    """Pre-compiled regex rules loaded from YAML."""

    def __init__(self, rules_path: Path = _RULES_PATH) -> None:
        self._compiled: list[tuple[dict, re.Pattern[str]]] = []
        self._load_rules(rules_path)

    def _load_rules(self, rules_path: Path) -> None:
        with open(rules_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for rule in data.get("rules", []):
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            self._compiled.append((rule, pattern))

    def check_rules(self, prompt: str) -> list[RuleMatch]:
        matches: list[RuleMatch] = []
        for rule, pattern in self._compiled:
            match = pattern.search(prompt)
            if match:
                matches.append(
                    RuleMatch(
                        rule_id=rule["id"],
                        severity=rule["severity"],
                        category=rule["category"],
                        matched_text=match.group(0),
                        description=rule["description"],
                    )
                )
        return matches


_rules_engine: RulesEngine | None = None


def get_rules_engine() -> RulesEngine:
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = RulesEngine()
    return _rules_engine


def check_rules(prompt: str) -> list[RuleMatch]:
    return get_rules_engine().check_rules(prompt)

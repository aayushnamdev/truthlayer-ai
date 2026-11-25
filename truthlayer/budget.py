"""Hard cost limit for AI calls. The ledger is a small JSON file; it never holds secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .settings import AISettings


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self, path: Path, ai: AISettings):
        self.path = Path(path)
        self.ai = ai
        self.data: dict[str, Any] = {"limit_usd": ai.cost_limit_usd, "max_calls": ai.max_calls, "spent_usd": 0.0,
                                     "calls": 0, "input_tokens": 0, "output_tokens": 0, "entries": []}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text()))
            except json.JSONDecodeError:
                raise ValueError(f"cost ledger {self.path} is damaged; fix or delete it") from None
        self.data["limit_usd"], self.data["max_calls"] = ai.cost_limit_usd, ai.max_calls

    # prices include the safety multiplier, so a wrong price guess still stays under the limit
    def _cost(self, tokens_in: float, tokens_out: float) -> float:
        m = self.ai.price_safety_multiplier
        return (tokens_in * self.ai.price_in_per_mtok + tokens_out * self.ai.price_out_per_mtok) * m / 1e6

    def estimate(self, prompt_chars: int, system_chars: int = 0) -> float:
        tin = (prompt_chars + system_chars) / self.ai.chars_per_token_estimate
        return self._cost(tin, self.ai.max_output_tokens)

    @property
    def spent(self) -> float:
        return float(self.data["spent_usd"])

    @property
    def remaining(self) -> float:
        return max(0.0, self.ai.cost_limit_usd - self.spent)

    def check(self, est: float) -> None:
        """Raise BudgetExceeded BEFORE a call that could pass the limit or the call cap."""
        if self.data["calls"] >= self.ai.max_calls:
            raise BudgetExceeded(f"call limit reached ({self.ai.max_calls} calls)")
        if self.spent + est > self.ai.cost_limit_usd:
            raise BudgetExceeded(f"next call could cost up to ${est:.4f}; spent ${self.spent:.4f} of ${self.ai.cost_limit_usd:.2f}")

    def charge(self, label: str, tokens_in: int | None, tokens_out: int | None, est: float, ok: bool) -> float:
        """Record one attempt. Real usage when the API reported it, otherwise the worst-case estimate."""
        cost = self._cost(tokens_in, tokens_out or 0) if tokens_in is not None else est
        self.data["spent_usd"] = round(self.spent + cost, 6)
        self.data["calls"] += 1
        self.data["input_tokens"] += tokens_in or 0
        self.data["output_tokens"] += tokens_out or 0
        self.data["entries"].append({"label": label, "input_tokens": tokens_in, "output_tokens": tokens_out,
                                     "charged_usd": round(cost, 6), "ok": ok, "real_usage": tokens_in is not None})
        self.save()
        return cost

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1))

    def real_cost_usd(self) -> float:
        """Cost at the assumed prices WITHOUT the safety multiplier (what we expect to be billed)."""
        e = self.data
        return round((e["input_tokens"] * self.ai.price_in_per_mtok + e["output_tokens"] * self.ai.price_out_per_mtok) / 1e6, 6)

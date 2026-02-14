from dataclasses import dataclass


@dataclass
class StatusEffect:
    type: str
    duration: float
    strength: float = 0.0

    def tick(self, dt: float) -> None:
        self.duration = max(0.0, self.duration - dt)

    @property
    def active(self) -> bool:
        return self.duration > 0.0

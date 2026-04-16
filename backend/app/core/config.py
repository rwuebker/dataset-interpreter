from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    simulate_stage_delay_seconds: float = 0.6


settings = Settings()

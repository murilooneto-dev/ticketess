from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ReportGenerateRequest(BaseModel):
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def _validate_range(self):
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("period_start deve ser anterior ou igual a period_end")
        return self


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period_start: date
    period_end: date
    created_at: datetime

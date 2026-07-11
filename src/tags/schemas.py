from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def _lowercase(cls, value: str) -> str:
        return value.lower()


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TagList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TagRead]

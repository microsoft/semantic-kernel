"""Class to hold usage results."""

from semantic_kernel.sk_pydantic import SKBaseModel


class UsageResult(SKBaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "UsageResult") -> "UsageResult":
        return UsageResult(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )

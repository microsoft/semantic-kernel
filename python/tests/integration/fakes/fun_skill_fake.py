# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition.sk_function_decorator import sk_function


# TODO: this fake skill is temporal usage.
# C# supports import skill from samples dir by using test helper and python should do the same
# `semantic-kernel/dotnet/src/IntegrationTests/TestHelpers.cs`
class FunSkillFake:
    @sk_function(
        description="Write a joke",
        name="WriteJoke",
    )
    def write_joke(self) -> str:
        return "WriteJoke"

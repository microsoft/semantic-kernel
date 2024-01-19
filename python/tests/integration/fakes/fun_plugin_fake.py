# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.plugin_definition.sk_function_decorator import sk_function


# TODO: this fake plugin is temporal usage.
# C# supports import plugin from samples dir by using test helper and python should do the same
# `semantic-kernel/dotnet/src/IntegrationTests/TestHelpers.cs`
class FunPluginFake:
    @sk_function(
        description="Write a joke",
        name="WriteJoke",
    )
    def write_joke(self) -> str:
        return "WriteJoke"

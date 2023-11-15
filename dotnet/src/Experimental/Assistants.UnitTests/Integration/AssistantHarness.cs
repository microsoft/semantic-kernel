// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST // Comment line to enable
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating assistants.
/// </summary>
/// <remarks>
/// Comment out DISABLEHOST definition to enable tests.
/// Not enabled by default.
/// </remarks>
[Trait("Category", "Integration Tests")]
[Trait("Feature", "Assistant")]
public sealed class AssistantHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    /// <summary>
    /// Test constructor.
    /// </summary>
    public AssistantHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantLifecycleAsync()
    {
        var assistant =
            await AssistantBuilder.NewAsync(
                apiKey: TestConfig.OpenAIApiKey,
                model: TestConfig.SupportedGpt35TurboModel,
                instructions: "say something funny",
                name: "Fred",
                description: "test assistant").ConfigureAwait(true);

        this.DumpAssistant(assistant);

        var copy =
            await AssistantBuilder.GetAssistantAsync(
                apiKey: TestConfig.OpenAIApiKey,
                assistantId: assistant.Id).ConfigureAwait(true);

        this.DumpAssistant(copy);
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantDefinitionAsync()
    {
        var assistant =
            await AssistantBuilder.FromTemplateAsync(
                apiKey: TestConfig.OpenAIApiKey,
                model: TestConfig.SupportedGpt35TurboModel,
                definitionPath: "Templates/PoetAssistant.yaml").ConfigureAwait(true);

        this.DumpAssistant(assistant);

        var copy =
            await AssistantBuilder.GetAssistantAsync(
                apiKey: TestConfig.OpenAIApiKey,
                assistantId: assistant.Id).ConfigureAwait(true);

        this.DumpAssistant(copy);
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantListAsync()
    {
        var context = new OpenAIRestContext(TestConfig.OpenAIApiKey);
        var assistants = await context.ListAssistantModelsAsync().ConfigureAwait(true);
        foreach (var assistant in assistants)
        {
            this.DumpAssistant(assistant);
        }
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantDeleteAsync()
    {
        var names =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "Fred",
                "Barney",
                "DeleteMe",
                "Poet",
                "Math Tutor",
            };

        var context = new OpenAIRestContext(TestConfig.OpenAIApiKey);
        var assistants = await context.ListAssistantModelsAsync().ConfigureAwait(true);
        foreach (var assistant in assistants)
        {
            if (!string.IsNullOrWhiteSpace(assistant.Name) && names.Contains(assistant.Name))
            {
                this._output.WriteLine($"Removing: {assistant.Name} - {assistant.Id}");
                await context.DeleteAssistantModelAsync(assistant.Id).ConfigureAwait(true);
            }
        }
    }

    private void DumpAssistant(AssistantModel assistant)
    {
        this._output.WriteLine($"# {assistant.Id}");
        this._output.WriteLine($"# {assistant.Model}");
        this._output.WriteLine($"# {assistant.Instructions}");
        this._output.WriteLine($"# {assistant.Name}");
        this._output.WriteLine($"# {assistant.Description}{Environment.NewLine}");
    }

    private void DumpAssistant(IAssistant assistant)
    {
        this._output.WriteLine($"# {assistant.Id}");
        this._output.WriteLine($"# {assistant.Model}");
        this._output.WriteLine($"# {assistant.Instructions}");
        this._output.WriteLine($"# {assistant.Name}");
        this._output.WriteLine($"# {assistant.Description}{Environment.NewLine}");
    }
}

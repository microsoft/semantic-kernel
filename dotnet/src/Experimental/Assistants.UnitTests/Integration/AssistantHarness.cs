// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating assistants.
/// </summary>
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
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistant =
            await context.CreateAssistantAsync(
                model: "gpt-3.5-turbo-1106",
                instructions: "say something funny",
                name: "Fred",
                description: "test assistant").ConfigureAwait(true);

        this.DumpAssistant(assistant);

        var copy = await context.GetAssistantAsync(assistant.Id).ConfigureAwait(true);

        this.DumpAssistant(copy);

        var modifiedCopy = await context.ModifyAssistantAsync(copy.Id, name: "Barney").ConfigureAwait(true);

        this.DumpAssistant(modifiedCopy);
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantDefinitionAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistant =
            await context.CreateAssistantAsync(
                model: "gpt-3.5-turbo-1106",
                configurationPath: "Templates/PoetAssistant.yaml").ConfigureAwait(true);

        this.DumpAssistant(assistant);

        var copy = await context.GetAssistantAsync(assistant.Id).ConfigureAwait(true);

        this.DumpAssistant(copy);
    }

    /// <summary>
    /// Verify creation and retrieval of assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyAssistantListAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistants = await context.ListAssistantsAsync().ConfigureAwait(true);
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
                "Poet",
                "Math Tutor",
            };
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistants = await context.ListAssistantsAsync().ConfigureAwait(true);
        foreach (var assistant in assistants)
        {
            if (!string.IsNullOrWhiteSpace(assistant.Name) && names.Contains(assistant.Name))
            {
                this._output.WriteLine($"Removing: {assistant.Name} - {assistant.Id}");
                await context.DeleteAssistantAsync(assistant.Id).ConfigureAwait(true);
            }
        }
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

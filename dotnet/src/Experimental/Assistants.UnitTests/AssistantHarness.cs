// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

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
    /// Test contructor.
    /// </summary>
    public AssistantHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task CreateAssistantAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var model =
            new AssistantModel
            {
                Name = "Fred",
                Description = "test assistant",
                Instructions = "say something funny",
                Model = "gpt-3.5-turbo-1106"
            };

        var assistant = await Assistant2.CreateAsync(context, model).ConfigureAwait(true);

        this._output.WriteLine($"# {assistant.Id}");
    }

    /// <summary>
    /// Retrieve an assistant.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task GetAssistantAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistant = await Assistant2.GetAsync(context, "asst_agi0P2OKJEBVrHN5Rcu0r2fy").ConfigureAwait(true);

        this._output.WriteLine($"# {assistant.Instructions}");
    }
}

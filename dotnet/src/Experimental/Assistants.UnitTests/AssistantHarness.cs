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
/// $$$
/// </summary>
public sealed class AssistantHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    public AssistantHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact(Skip = SkipReason)]
    public async Task CreateAssistantAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.Create(httpClient);

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

    [Fact(Skip = SkipReason)]
    public async Task GetAssistantAsync()
    {
    }
}

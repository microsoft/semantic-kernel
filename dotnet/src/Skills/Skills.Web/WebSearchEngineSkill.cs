// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public class WebSearchEngineSkill
{
    private readonly IWebSearchEngineAdapter _adapter;

    public WebSearchEngineSkill(IWebSearchEngineAdapter adapter)
    {
        this._adapter = adapter;
    }

    [SKFunction("Perform a web search.")]
    [SKFunctionInput(Description = "Text to search for")]
    public async Task<string> SearchAsync(string query, SKContext context)
    {
        string result = await this._adapter.SearchAsync(query, context.CancellationToken).ConfigureAwait(false);
        if (string.IsNullOrWhiteSpace(result))
        {
            context.Fail("Failed to get a response from the web search engine.");
        }

        return result;
    }
}

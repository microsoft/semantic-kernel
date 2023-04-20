// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public class WebSearchEngineSkill
{
    public static class Parameters
    {
        /// <summary>
        /// Number of results.
        /// </summary>
        public const string Count = "count";

        /// <summary>
        /// Number of results to skip.
        /// </summary>
        public const string Offset = "offset";         
    }

    private const string DefaultCount = "1";
    private const string DefaultOffset = "0";

    private readonly IWebSearchEngineConnector _connector;

    public WebSearchEngineSkill(IWebSearchEngineConnector connector)
    {
        this._connector = connector;
    }

    [SKFunction("Perform a web search.")]
    [SKFunctionInput(Description = "Text to search for")]
    [SKFunctionContextParameter(Name = Parameters.Count, Description = "Number of results")]
    [SKFunctionContextParameter(Name = Parameters.Offset, Description = "Number of results to skip")]
    public async Task<string> SearchAsync(string query, SKContext context)
    {
        var count = context.Variables.ContainsKey(Parameters.Count) ? context[Parameters.Count] : "1";        
        if (string.IsNullOrWhiteSpace(count)) { count = DefaultCount; }

        var offset = context.Variables.ContainsKey(Parameters.Offset) ? context[Parameters.Offset] : "1";
        if (string.IsNullOrWhiteSpace(offset)) { offset = DefaultOffset; }

        int countInt = int.Parse(count, CultureInfo.InvariantCulture);
        int offsetInt = int.Parse(offset, CultureInfo.InvariantCulture);
        var  results = await this._connector.SearchAsync(query, countInt, offsetInt, context.CancellationToken);
        if (!results.Any())
        {
            context.Fail("Failed to get a response from the web search engine.");
        }

        string resultString;
        if (countInt == 1)
        {
            var result = results.FirstOrDefault();
            resultString = result ?? string.Empty;
        }
        else
        {
            resultString = JsonSerializer.Serialize(results.Select(x => x));
        }

        return resultString;
    }
}

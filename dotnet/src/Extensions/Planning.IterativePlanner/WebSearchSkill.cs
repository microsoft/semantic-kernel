// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Web;

namespace Planning.IterativePlanner;

//TODO: This is a copy of WebSearchEngineSkill, the only difference is the SKFunction attribute.
// I am ashamed for this, but I needed to change the description as it is a part of the prompt which I needed to tune 
// we should discuss the options and the possible solutions
// tried overloading but got this error :
// Function overload not supported: Function overloads are not supported, please differentiate function names
// one solution would be to crete our Agents and Create a wrapper around Skills / Functions and call them
// tools or plugins, which would offer a possibility to adjust the description used for the prompt
public class WebSearchSkill 
{
    private readonly WebSearchEngineSkill _webSearchEngineSkill;
    private const string DefaultCount = "1";
    private const string DefaultOffset = "0";
  
    public WebSearchSkill(IWebSearchEngineConnector connector) 
    {
        this._webSearchEngineSkill = new WebSearchEngineSkill(connector);
    }

    [SKFunction("A search engine. Useful for when you need to answer questions about current events. Input should be a search query.")]
    [SKFunctionName("Search")]
    [SKFunctionInput(Description = "Text to search for")]
    [SKFunctionContextParameter(Name = WebSearchEngineSkill.CountParam, Description = "Number of results", DefaultValue = DefaultCount)]
    [SKFunctionContextParameter(Name = WebSearchEngineSkill.OffsetParam, Description = "Number of results to skip", DefaultValue = DefaultOffset)]
    public async Task<string> SearchAsync(string query, SKContext context)
    {
        return await this._webSearchEngineSkill.SearchAsync(query, context).ConfigureAwait(false);
    }
}

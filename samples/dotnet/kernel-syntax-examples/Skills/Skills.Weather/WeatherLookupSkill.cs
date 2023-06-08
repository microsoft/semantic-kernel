// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Skills.Weather;
namespace Skills;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public class WeatherLookupSkill
{
    private readonly IWeatherApiConnector _connector;

    public WeatherLookupSkill(IWeatherApiConnector connector)
    {
        this._connector = connector;
    }

    [SKFunction("Lookup the current weather for a location.")]
    [SKFunctionName("LookupWeather")]
    [SKFunctionInput(Description = "Location to get the weather for.")]
    public async Task<string> SearchAsync(string location, SKContext context)
    {
        IEnumerable<string> results = await this._connector.LookupWeatherAsync(location);
        return results.FirstOrDefault();
    }
}

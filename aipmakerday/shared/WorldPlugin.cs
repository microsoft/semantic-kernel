namespace SemanticKernel.HelloAgents.Internal;

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using System.ComponentModel;

internal sealed class WorldPlugin(ILoggerFactory loggerFactory)
{
    private readonly ILogger logger = loggerFactory.CreateLogger<WorldPlugin>();

    [KernelFunction]
    [Description("Returns the current date and time for the current time zone.")]
    public DateTime Now()
    {
        return DateTime.Now;
    }

    [KernelFunction]
    [Description("Provides the information about the current location (permission already granted).")]
    public async Task<string> WhereAsync()
    {
        using HttpClient client = new();
        var response = await client.GetAsync("https://reallyfreegeoip.org/json/");
        return await response.Content.ReadAsStringAsync();
    }

    [KernelFunction]
    [Description("Provides the weather for the requested city name or postal code.")]
    public async Task<string> WeatherAsync(
        [param:Description("A real city name or postal code for the requested location (never \"current\").")]
        string location)
    {
        this.logger.LogInformation($"Function WorldPlugin-Weather: {location}");
        using HttpClient client = new();
        var response = await client.GetAsync($"https://wttr.in/{location}?format=j1");
        return await response.Content.ReadAsStringAsync();
    }
}

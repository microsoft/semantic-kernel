using System.Net;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;
using Models;

#pragma warning disable CA1822

public class AIPluginJson
{
    [Function("GetAIPluginJson")]
    public HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = ".well-known/ai-plugin.json")] HttpRequestData req)
    {
        if (req is null)
        {
            throw new System.ArgumentNullException(nameof(req));
        }

        var currentDomain = $"{req.Url.Scheme}://{req.Url.Host}:{req.Url.Port}";

        HttpResponseData response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "application/json");

        var appSettings = AppSettings.LoadSettings();

        // serialize app settings to json using System.Text.Json
        var json = System.Text.Json.JsonSerializer.Serialize(appSettings.AIPlugin);

        // replace {url} with the current domain
        json = json.Replace("{url}", currentDomain, StringComparison.OrdinalIgnoreCase);

        response.WriteString(json);

        return response;
    }
}

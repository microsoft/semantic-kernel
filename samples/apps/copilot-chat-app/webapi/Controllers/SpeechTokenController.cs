// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Controllers;

/// <summary>
/// Token Response is a simple wrapper around the token and region
/// </summary>
public class SpeechTokenResponse
{
    public string? token { get; set; }
    public string? region { get; set; }
}

[ApiController]
public class SpeechTokenController : ControllerBase
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<SpeechTokenController> _logger;

    public SpeechTokenController(IConfiguration configuration, ILogger<SpeechTokenController> logger)
    {
        this._configuration = configuration;
        this._logger = logger;
    }

    /// <summary>
    /// Use the Azure Speech Config key to return an authorization token and region as a Token Response.
    /// </summary>
    [Route("speechToken")]
    [HttpGet]
    public ActionResult<SpeechTokenResponse> Get()
    {
        AzureSpeechServiceConfig azureSpeechConfig = this._configuration.GetSection("AzureSpeechConfig").Get<AzureSpeechServiceConfig>();

        string FetchTokenUri = "https://" + azureSpeechConfig.Region + ".api.cognitive.microsoft.com/sts/v1.0/issueToken";
        string subscriptionKey = azureSpeechConfig.Key;

        var token = this.FetchTokenAsync(FetchTokenUri, subscriptionKey).Result;

        return new SpeechTokenResponse { token = token, region = azureSpeechConfig.Region };
    }

    private async Task<string> FetchTokenAsync(string fetchUri, string subscriptionKey)
    {
        // TODO: get the HttpClient from the DI container
        using (var client = new HttpClient())
        {
            client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);
            UriBuilder uriBuilder = new UriBuilder(fetchUri);

            var result = await client.PostAsync(uriBuilder.Uri, null);
            result.EnsureSuccessStatusCode();
            this._logger.LogDebug("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);
            return await result.Content.ReadAsStringAsync();
        }
    }
}

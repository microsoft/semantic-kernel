// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Controllers;

/// <summary>
/// Token Response is a simple wrapper around the token and region
/// </summary>
public class SpeechTokenResponse
{
    public string? Token { get; set; }
    public string? Region { get; set; }
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
        AzureSpeechConfig azureSpeech = this._configuration.GetSection("AzureSpeech").Get<AzureSpeechConfig>();

        string fetchTokenUri = "https://" + azureSpeech.Region + ".api.cognitive.microsoft.com/sts/v1.0/issueToken";
        string subscriptionKey = azureSpeech.Key;

        var token = this.FetchTokenAsync(fetchTokenUri, subscriptionKey).Result;

        return new SpeechTokenResponse { Token = token, Region = azureSpeech.Region };
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

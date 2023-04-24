// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;

namespace SemanticKernel.Service.Controllers;

[Authorize]
[ApiController]
public class SpeechTokenController : ControllerBase
{
    private readonly ILogger<SpeechTokenController> _logger;
    private readonly AzureSpeechOptions _config;

    public SpeechTokenController(IOptions<AzureSpeechOptions> config, ILogger<SpeechTokenController> logger)
    {
        this._logger = logger;
        this._config = config.Value;
    }

    /// <summary>
    /// Get an authorization token and region
    /// </summary>
    [Route("speechToken")]
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<ActionResult<SpeechTokenResponse>> GetAsync()
    {
        if (string.IsNullOrWhiteSpace(this._config.Region))
        {
            throw new InvalidOperationException($"Missing value for {AzureSpeechOptions.PropertyName}:{nameof(this._config.Region)}");
        }

        string fetchTokenUri = $"https://{this._config.Region}.api.cognitive.microsoft.com/sts/v1.0/issueToken";
        string token = await this.FetchTokenAsync(fetchTokenUri, this._config.Key).ConfigureAwait(false);
        return new SpeechTokenResponse { Token = token, Region = this._config.Region };
    }

    private async Task<string> FetchTokenAsync(string fetchUri, string subscriptionKey)
    {
        // TODO: get the HttpClient from the DI container
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);
        UriBuilder uriBuilder = new(fetchUri);

        var result = await client.PostAsync(uriBuilder.Uri, null);
        result.EnsureSuccessStatusCode();
        this._logger.LogDebug("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);
        return await result.Content.ReadAsStringAsync();
    }
}

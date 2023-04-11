
// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Controllers;

public class TokenResponse
{
    public string? token { get; set; }
    public string? region { get; set; }
}

[ApiController]
public class TokenController : ControllerBase
{
    private readonly IConfiguration _configuration;

    public TokenController(IConfiguration configuration)
    {
        this._configuration = configuration;
    }

    [Route("speech")]
    [HttpGet]
    public ActionResult<TokenResponse> Get()
    {
        AzureSpeechServiceConfig azureSpeechConfig = this._configuration.GetSection("AzureSpeechConfig").Get<AzureSpeechServiceConfig>();

        if (true)
        {
            string FetchTokenUri = "https://" + azureSpeechConfig.Region + ".api.cognitive.microsoft.com/sts/v1.0/issueToken";
            string subscriptionKey = azureSpeechConfig.Key;

            var token = this.FetchTokenAsync(FetchTokenUri, subscriptionKey).Result;

            return new TokenResponse { token = token, region = azureSpeechConfig.Region };
        }
        //else
        //{
        //    var speechConfig = SpeechConfig.FromSubscription(azureSpeechConfig.Key, azureSpeechConfig.Region);
        //    speechConfig.SpeechRecognitionLanguage = "en-US";

        //    using var audioConfig = AudioConfig.FromDefaultMicrophoneInput();
        //    var speechRecognizer = new SpeechRecognizer(speechConfig, audioConfig);

        //    return speechRecognizer;
        //}
    }

    private async Task<string> FetchTokenAsync(string fetchUri, string subscriptionKey)
    {
        using (var client = new HttpClient())
        {
            client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);
            UriBuilder uriBuilder = new UriBuilder(fetchUri);
            //var result = await client.PostAsync(uriBuilder.Uri.AbsoluteUri, null);
            //Console.WriteLine("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);

            var result = await client.PostAsync(uriBuilder.Uri, null);
            Console.WriteLine("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);
            return await result.Content.ReadAsStringAsync();
        }
    }
}

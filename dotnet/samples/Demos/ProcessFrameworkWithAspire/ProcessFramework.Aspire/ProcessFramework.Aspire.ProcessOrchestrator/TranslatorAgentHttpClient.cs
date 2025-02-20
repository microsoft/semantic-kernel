// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using ProcessFramework.Aspire.Shared;

namespace ProcessFramework.Aspire.ProcessOrchestrator;

public class TranslatorAgentHttpClient(HttpClient httpClient)
{
    private static readonly Uri s_agentUri = new("/api/translatoragent");

    public async Task<string> TranslateAsync(string textToTranslate)
    {
        var payload = new TranslationRequest { TextToTranslate = textToTranslate };
        var response = await httpClient.PostAsync(s_agentUri, new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json")).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        var responseContent = await response.Content.ReadAsStringAsync();
        return responseContent;
    }
}

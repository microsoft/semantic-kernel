using System;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.Shared;

namespace ProcessFramework.Aspire.ProcessOrchestrator;

public class TranslatorAgentHttpClient(HttpClient httpClient)
{
    public async Task<string> TranslateAsync(string textToTranslate)
    {
        var payload = new TranslationRequest { TextToTranslate = textToTranslate };
        var response = await httpClient.PostAsync("/api/translatoragent", new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json")).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        var responseContent = await response.Content.ReadAsStringAsync();
        return responseContent;
    }
}

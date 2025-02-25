// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using ProcessFramework.Aspire.Shared;

namespace ProcessFramework.Aspire.ProcessOrchestrator;

public class TranslatorAgentHttpClient(HttpClient httpClient)
{
    public async Task<string> TranslateAsync(string textToTranslate)
    {
        var payload = new TranslationRequest { TextToTranslate = textToTranslate };
#pragma warning disable CA2234 // We cannot pass uri here since we are using a customer http client with a base address
        var response = await httpClient.PostAsync("/api/translator", new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json")).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        var responseContent = await response.Content.ReadAsStringAsync();
        return responseContent;
    }
}

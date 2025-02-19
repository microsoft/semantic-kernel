// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using ProcessFramework.Aspire.Shared;

namespace ProcessFramework.Aspire.ProcessOrchestrator;

public class SummaryAgentHttpClient(HttpClient httpClient)
{
    private static readonly Uri s_agentUri = new("/api/summaryagent");

    public async Task<string> SummarizeAsync(string textToSummarize)
    {
        var payload = new SummarizeRequest { TextToSummarize = textToSummarize };
        var response = await httpClient.PostAsync(s_agentUri, new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
        response.EnsureSuccessStatusCode();
        var responseContent = await response.Content.ReadAsStringAsync();
        return responseContent;
    }
}

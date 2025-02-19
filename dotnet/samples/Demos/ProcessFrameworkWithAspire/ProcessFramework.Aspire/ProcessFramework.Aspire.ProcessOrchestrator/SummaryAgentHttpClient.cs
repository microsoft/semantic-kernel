using System;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.Shared;

namespace ProcessFramework.Aspire.ProcessOrchestrator;

public class SummaryAgentHttpClient(HttpClient httpClient)
{
    public async Task<string> SummarizeAsync(string textToSummarize)
    {
        var payload = new SummarizeRequest { TextToSummarize = textToSummarize };
        var response = await httpClient.PostAsync("/api/summaryagent", new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
        response.EnsureSuccessStatusCode();
        var responseContent = await response.Content.ReadAsStringAsync();
        return responseContent;
    }
}

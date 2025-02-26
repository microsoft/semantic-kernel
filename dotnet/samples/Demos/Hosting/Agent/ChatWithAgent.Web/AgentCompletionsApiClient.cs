// Copyright (c) Microsoft. All rights reserved.

namespace ChatWithAgent.Web;

public class AgentCompletionsApiClient(HttpClient httpClient)
{
    public async Task<string> CompleteAsync(string prompt, CancellationToken cancellationToken)
    {
        var result = await httpClient.PostAsJsonAsync<AgentCompletionRequest>("/agent/completions", new AgentCompletionRequest() { Prompt = prompt }, cancellationToken).ConfigureAwait(false);

        return await result.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
    }
}

/// <summary>
/// The agent completion request model.
/// </summary>
public class AgentCompletionRequest
{
    /// <summary>
    /// Gets or sets the prompt.
    /// </summary>
    public required string Prompt { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether streaming is requested.
    /// </summary>
    public bool IsStreaming { get; set; }
}

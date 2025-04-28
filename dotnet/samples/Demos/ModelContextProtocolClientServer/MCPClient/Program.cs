// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using MCPClient.Samples;

namespace MCPClient;

internal sealed class Program
{
    /// <summary>
    /// Main method to run all the samples.
    /// </summary>
    public static async Task Main(string[] args)
    {
        await AzureAIAgentWithMCPToolsSample.RunAsync();

        await AgentAvailableAsMCPToolSample.RunAsync();
    }
}

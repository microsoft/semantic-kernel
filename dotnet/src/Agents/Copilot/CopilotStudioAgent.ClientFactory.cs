// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents.Copilot;

/// <summary>
/// Provides an <see cref="CopilotClient"/> for use by <see cref="CopilotStudioAgent"/>.
/// </summary>
public sealed partial class CopilotStudioAgent : Agent
{
    private const string CopilotStudioHttpClientName = nameof(CopilotStudioAgent);

    /// <summary>
    /// Creates a new instance of <see cref="CopilotClient"/> configured with the provided settings and an optional logger.
    /// </summary>
    /// <param name="settings">The connection settings for Copilot Studio.</param>
    /// <param name="logger">An optional logger for logging purposes.</param>
    /// <returns>A configured instance of <see cref="CopilotClient"/>.</returns>
    public static CopilotClient CreateClient(CopilotStudioConnectionSettings settings, ILogger? logger = null)
    {
        ServiceCollection services = new();

        services
            .AddSingleton(settings)
            .AddSingleton<CopilotStudioTokenHandler>()
            .AddHttpClient(CopilotStudioHttpClientName)
            .ConfigurePrimaryHttpMessageHandler<CopilotStudioTokenHandler>();

        IHttpClientFactory httpClientFactory =
            services
                .BuildServiceProvider()
                .GetRequiredService<IHttpClientFactory>();

        CopilotClient client = new(settings, httpClientFactory, logger ?? NullLogger.Instance, CopilotStudioHttpClientName);

        return client;
    }
}

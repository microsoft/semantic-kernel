// Copyright (c) Microsoft. All rights reserved.
// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Extensions;

using Client;
using Microsoft.Extensions.DependencyInjection;


/// <summary>
///  Extensions for the service collection.
/// </summary>
public static class ServiceCollectionExtensions
{
    public const string SourceGraphBaseUrl = "https://sourcegraph.com/.api";
    public const string SourceGraphGraphAPIEndpoint = "/graphql";
    public const string SourceGraphStreamingSearchAPIEndpoint = "/search/stream";
    public const string SourceGraphStreamingCompletionsAPIEndpoint = "/completions/stream";
    public const string SourceGraphCodeCompletionsEndpoint = "/completions/code";


    /// <summary>
    ///  Adds the SourceGraph client to the service collection.
    /// </summary>
    /// <param name="services"></param>
    /// <param name="accessToken"></param>
    /// <param name="endpoint"></param>
    /// <param name="withStreaming"></param>
    /// <returns></returns>
    public static IServiceCollection AddSourceGraphClient(this IServiceCollection services, SourceGraphClientOptions options, bool withStreaming = false)
    {
        services.AddSourceGraphClient()
            .ConfigureHttpClient(client =>
            {
                client.BaseAddress = new Uri(options.ServerEndpoint + SourceGraphGraphAPIEndpoint);
                client.DefaultRequestHeaders.Add("Authorization", $"token {options.AccessToken}");
                client.DefaultRequestHeaders.Add("Connection", "keep-alive");
                client.MaxResponseContentBufferSize = 1_000_000;
                client.Timeout = TimeSpan.FromMinutes(3);
            });
        services.AddSingleton<ISourceGraphStreamClient, SourceGraphStreamingClient>(provider => new SourceGraphStreamingClient(options));
        services.AddSingleton<ISourceGraphQLClient, SourceGraphGraphQLClient>(provider =>
        {
            var sourceGraphClient = provider.GetRequiredService<ISourceGraphClient>();
            return new SourceGraphGraphQLClient(sourceGraphClient);
        });

        services.AddSingleton<ISourceGraphSearchClient, SourceGraphSearchClient>(provider =>
        {
            var sourceGraphClient = provider.GetRequiredService<ISourceGraphClient>();
            return new SourceGraphSearchClient(sourceGraphClient);
        });

        services.AddSingleton<ISourceGraphGitClient, SourceGraphGitClient>(provider =>
        {
            var sourceGraphClient = provider.GetRequiredService<ISourceGraphClient>();
            return new SourceGraphGitClient(sourceGraphClient);
        });

        services.AddSingleton<ISourceGraphCompletionsClient, SourceGraphCompletionsClient>(provider =>
        {
            var sourceGraphClient = provider.GetRequiredService<ISourceGraphClient>();
            var sourceGraphStreamClient = provider.GetRequiredService<ISourceGraphStreamClient>();
            return new SourceGraphCompletionsClient("anthropic", options.AccessToken, sourceGraphClient, sourceGraphStreamClient);
        });
        return services;
    }

}

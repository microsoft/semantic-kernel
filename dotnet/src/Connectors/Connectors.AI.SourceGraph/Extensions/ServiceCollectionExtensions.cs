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
    public const string SourceGraphGraphAPI = "https://sourcegraph.com/.api/graphql";


    /// <summary>
    ///  Adds the SourceGraph client to the service collection.
    /// </summary>
    /// <param name="services"></param>
    /// <param name="accessToken"></param>
    /// <returns></returns>
    public static IServiceCollection AddSourceGraphClient(this IServiceCollection services, string accessToken = "")
    {
        SourceGraphClientServiceCollectionExtensions.AddSourceGraphClient(services)
            .ConfigureHttpClient(client =>
            {
                client.BaseAddress = new Uri(SourceGraphGraphAPI);
                client.DefaultRequestHeaders.Add("Authorization", $"token {accessToken}");
                client.MaxResponseContentBufferSize = 1_000_000;
            });

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

        return services;
    }

}

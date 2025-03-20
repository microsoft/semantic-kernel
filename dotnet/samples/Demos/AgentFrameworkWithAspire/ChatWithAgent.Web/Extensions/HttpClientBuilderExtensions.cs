// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Http.Resilience;

namespace ChatWithAgent.Web;

/// <summary>
/// Provider extension methods to <see cref="IHttpClientBuilder"/>
/// </summary>
public static class HttpClientBuilderExtensions
{
#pragma warning disable EXTEXP0001
    /// <summary>
    /// Remove already configured resilience handlers
    /// </summary>
    /// <param name="builder">The builder instance.</param>
    /// <returns>The value of <paramref name="builder" />.</returns>
    /// <remarks>For more details, see https://github.com/dotnet/extensions/issues/4814#issuecomment-2374345866</remarks>
    public static IHttpClientBuilder ClearResilienceHandlers(this IHttpClientBuilder builder)
    {
        builder.ConfigureAdditionalHttpMessageHandlers(static (handlers, _) =>
        {
            for (int i = 0; i < handlers.Count;)
            {
                if (handlers[i] is ResilienceHandler)
                {
                    handlers.RemoveAt(i);
                    continue;
                }
                i++;
            }
        });
        return builder;
    }
#pragma warning restore EXTEXP0001
}

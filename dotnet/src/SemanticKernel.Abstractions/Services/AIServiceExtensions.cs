// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Extension methods for <see cref="IAIService"/>.
/// </summary>
public static class AIServiceExtensions
{
    /// <summary>
    /// Key used to store the model identifier in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public const string ModelIdKey = "ModelId";

    /// <summary>
    /// Key used to store the endpoint key in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public const string EndpointKey = "Endpoint";

    /// <summary>
    /// Key used to store the API version in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public const string ApiVersionKey = "ApiVersion";

    /// <summary>
    /// Gets the model identifier from <paramref name="service"/>'s <see cref="IAIService.Attributes"/>.
    /// </summary>
    /// <param name="service">The service from which to get the model identifier.</param>
    /// <returns>The model identifier if it was specified in the service's attributes; otherwise, null.</returns>
    public static string? GetModelId(this IAIService service) => service.GetAttribute(ModelIdKey);

    /// <summary>
    /// Gets the endpoint from <paramref name="service"/>'s <see cref="IAIService.Attributes"/>.
    /// </summary>
    /// <param name="service">The service from which to get the endpoint.</param>
    /// <returns>The endpoint if it was specified in the service's attributes; otherwise, null.</returns>
    public static string? GetEndpoint(this IAIService service) => service.GetAttribute(EndpointKey);

    /// <summary>
    /// Gets the API version from <paramref name="service"/>'s <see cref="IAIService.Attributes"/>
    /// </summary>
    /// <param name="service">The service from which to get the API version.</param>
    /// <returns>The API version if it was specified in the service's attributes; otherwise, null.</returns>
    public static string? GetApiVersion(this IAIService service) => service.GetAttribute(ApiVersionKey);

    /// <summary>
    /// Gets the specified attribute.
    /// </summary>
    private static string? GetAttribute(this IAIService service, string key)
    {
        Verify.NotNull(service);
        return service.Attributes?.TryGetValue(key, out object? value) == true ? value as string : null;
    }
}

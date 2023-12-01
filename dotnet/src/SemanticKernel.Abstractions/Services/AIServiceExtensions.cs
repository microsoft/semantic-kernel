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
    /// Gets the model identifier.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetModelId(this IAIService service)
    {
        return service.GetAttribute(ModelIdKey);
    }

    /// <summary>
    /// Gets the endpoint.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetEndpoint(this IAIService service)
    {
        return service.GetAttribute(EndpointKey);
    }

    /// <summary>
    /// Gets the API version.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetApiVersion(this IAIService service)
    {
        return service.GetAttribute(ApiVersionKey);
    }

    /// <summary>
    /// Gets the specified attribute.
    /// </summary>
    /// <param name="service"></param>
    /// <param name="key"></param>
    /// <returns></returns>
    public static string? GetAttribute(this IAIService service, string key)
    {
        return service.Attributes?.TryGetValue(key, out var value) == true ? value as string : null;
    }
}

// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Extension menthods for <see cref="AIServiceAttributes"/>.
/// </summary>
public static class IAIServiceExtensions
{
    /// <summary>
    /// Gets the model identifier.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetModelId(this IAIService service)
    {
        return service.GetAttributes<AIServiceAttributes>()?.ModelId;
    }

    /// <summary>
    /// Gets the endpoint.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetEndpoint(this IAIService service)
    {
        return service.GetAttributes<AIServiceAttributes>()?.Endpoint;
    }

    /// <summary>
    /// Gets the API version.
    /// </summary>
    /// <param name="service"></param>
    /// <returns></returns>
    public static string? GetApiVersion(this IAIService service)
    {
        return service.GetAttributes<AIServiceAttributes>()?.ApiVersion;
    }

    /// <summary>
    /// Gets the specified attribute.
    /// </summary>
    /// <param name="service"></param>
    /// <param name="key"></param>
    /// <returns></returns>
    public static string? GetAttribute(this IAIService service, string key)
    {
        var attributes = service.GetAttributes<AIServiceAttributes>();
        return attributes?.Attributes.ContainsKey(key) == true ? attributes.Attributes[key] as string : null;
    }
}

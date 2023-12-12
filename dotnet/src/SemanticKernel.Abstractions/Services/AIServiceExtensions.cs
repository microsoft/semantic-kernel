// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1716 // Identifiers should not match keywords

using System.Linq;
using System.Text;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Extension methods for <see cref="IAIService"/>.
/// </summary>
public static class AIServiceExtensions
{
    /// <summary>
    /// Gets the key used to store the model identifier in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string ModelIdKey => "ModelId";

    /// <summary>
    /// Gets the key used to store the endpoint key in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string EndpointKey => "Endpoint";

    /// <summary>
    /// Gets the key used to store the API version in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string ApiVersionKey => "ApiVersion";

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

    /// <summary>
    /// Resolves an <see cref="IAIService"/> and associated <see cref="PromptExecutionSettings"/> from the specified
    /// <see cref="Kernel"/> based on a <see cref="KernelFunction"/> and associated <see cref="KernelArguments"/>.
    /// </summary>
    /// <typeparam name="T">
    /// Specifies the type of the <see cref="IAIService"/> required. This must be the same type
    /// with which the service was registered in the <see cref="IServiceCollection"/> orvia
    /// the <see cref="IKernelBuilder"/>.
    /// </typeparam>
    /// <param name="selector">The <see cref="IAIServiceSelector"/> to use to select a service from the <see cref="Kernel"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The function.</param>
    /// <param name="arguments">The function arguments.</param>
    /// <returns>A tuple of the selected service and the settings associated with the service (the settings may be null).</returns>
    /// <exception cref="KernelException">An appropriate service could not be found.</exception>
    public static (T?, PromptExecutionSettings?) SelectAIService<T>(
        this IAIServiceSelector selector,
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments) where T : class, IAIService
    {
        Verify.NotNull(selector);
        Verify.NotNull(kernel);
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        if (selector.TrySelectAIService<T>(
            kernel, function, arguments,
            out T? service, out PromptExecutionSettings? settings))
        {
            return (service, settings);
        }

        var message = new StringBuilder($"Required service of type {typeof(T)} not registered.");
        if (function.ExecutionSettings is not null)
        {
            string serviceIds = string.Join("|", function.ExecutionSettings.Select(model => model.ServiceId));
            if (!string.IsNullOrEmpty(serviceIds))
            {
                message.Append($" Expected serviceIds: {serviceIds}.");
            }

            string modelIds = string.Join("|", function.ExecutionSettings.Select(model => model.ModelId));
            if (!string.IsNullOrEmpty(modelIds))
            {
                message.Append($" Expected modelIds: {modelIds}.");
            }
        }

        throw new KernelException(message.ToString());
    }
}

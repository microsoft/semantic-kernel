// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Implementation of <see cref="IAIServiceSelector"/> that selects the AI service based on the order of the execution settings.
/// Uses the service id or model id to select the preferred service provider and then returns the service and associated execution settings.
/// </summary>
internal sealed class OrderedAIServiceSelector : IAIServiceSelector, IChatClientSelector
{
    public static OrderedAIServiceSelector Instance { get; } = new();

    /// <inheritdoc/>
    [Experimental("SKEXP0001")]
    public bool TrySelectChatClient<T>(Kernel kernel, KernelFunction function, KernelArguments arguments, [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings) where T : class, IChatClient
        => this.TrySelect(kernel, function, arguments, out service, out serviceSettings);

    /// <inheritdoc/>
    public bool TrySelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments, [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings) where T : class, IAIService
        => this.TrySelect(kernel, function, arguments, out service, out serviceSettings);

    private bool TrySelect<T>(
        Kernel kernel, KernelFunction function, KernelArguments arguments,
        [NotNullWhen(true)] out T? service,
        out PromptExecutionSettings? serviceSettings) where T : class
    {
        // Allow the execution settings from the kernel arguments to take precedence
        var executionSettings = arguments.ExecutionSettings ?? function.ExecutionSettings;
        if (executionSettings is null || executionSettings.Count == 0)
        {
            service = GetAnyService(kernel);
            if (service is not null)
            {
                serviceSettings = null;
                return true;
            }
        }
        else
        {
            PromptExecutionSettings? defaultExecutionSettings = null;
            // Search by service id first
            foreach (var keyValue in executionSettings)
            {
                var settings = keyValue.Value;
                var serviceId = keyValue.Key;
                if (string.IsNullOrEmpty(serviceId) || serviceId!.Equals(PromptExecutionSettings.DefaultServiceId, StringComparison.OrdinalIgnoreCase))
                {
                    defaultExecutionSettings ??= settings;
                }
                else if (!string.IsNullOrEmpty(serviceId))
                {
                    service = (kernel.Services as IKeyedServiceProvider)?.GetKeyedService<T>(serviceId);
                    if (service is not null)
                    {
                        serviceSettings = settings;
                        return true;
                    }
                }
            }

            // Search by model id next
            foreach (var keyValue in executionSettings)
            {
                var settings = keyValue.Value;
                var serviceId = keyValue.Key;
                if (!string.IsNullOrEmpty(settings.ModelId))
                {
                    service = this.GetServiceByModelId<T>(kernel, settings.ModelId!);
                    if (service is not null)
                    {
                        serviceSettings = settings;
                        return true;
                    }
                }
            }

            // Search for default service id last
            if (defaultExecutionSettings is not null)
            {
                service = GetAnyService(kernel);
                if (service is not null)
                {
                    serviceSettings = defaultExecutionSettings;
                    return true;
                }
            }
        }

        service = null;
        serviceSettings = null;
        return false;

        // Get's a non-required service, regardless of service key
        static T? GetAnyService(Kernel kernel) =>
            kernel.Services is IKeyedServiceProvider ?
                kernel.GetAllServices<T>().LastOrDefault() : // see comments in Kernel/KernelBuilder for why we can't use GetKeyedService
                kernel.Services.GetService<T>();
    }

    private T? GetServiceByModelId<T>(Kernel kernel, string modelId) where T : class
    {
        foreach (var service in kernel.GetAllServices<T>())
        {
            string? serviceModelId = null;
            if (service is IAIService aiService)
            {
                serviceModelId = aiService.GetModelId();
            }
            else if (service is IChatClient chatClient)
            {
                serviceModelId = chatClient.GetModelId();
            }

            if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId == modelId)
            {
                return service;
            }
        }

        return null;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Implementation of <see cref="IAIServiceSelector"/> that selects the AI service based on the order of the execution settings.
/// Uses the service id or model id to select the preferred service provider and then returns the service and associated execution settings.
/// </summary>
internal sealed class OrderedAIServiceSelector : IAIServiceSelector
{
    public static OrderedAIServiceSelector Instance { get; } = new();

    /// <inheritdoc/>
    public (T?, PromptExecutionSettings?) SelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments) where T : class, IAIService
    {
        var executionSettings = function.ExecutionSettings;
        if (executionSettings is null || executionSettings.Count == 0)
        {
            var service = kernel.Services is IKeyedServiceProvider ?
                kernel.GetAllServices<T>().LastOrDefault() : // see comments in Kernel/KernelBuilder for why we can't use GetKeyedService
                kernel.Services.GetService<T>();
            if (service is not null)
            {
                return (service, null);
            }
        }
        else
        {
            PromptExecutionSettings? defaultExecutionSettings = null;
            foreach (var settings in executionSettings)
            {
                if (!string.IsNullOrEmpty(settings.ServiceId))
                {
                    var service = kernel.Services is IKeyedServiceProvider ?
                        kernel.Services.GetKeyedService<T>(settings.ServiceId) :
                        null;
                    if (service is not null)
                    {
                        return (service, settings);
                    }
                }
                else if (!string.IsNullOrEmpty(settings.ModelId))
                {
                    var service = this.GetServiceByModelId<T>(kernel, settings.ModelId!);
                    if (service is not null)
                    {
                        return (service, settings);
                    }
                }
                else
                {
                    // First execution settings with empty or null service id is the default
                    defaultExecutionSettings ??= settings;
                }
            }

            if (defaultExecutionSettings is not null)
            {
                return (kernel.GetRequiredService<T>(), defaultExecutionSettings);
            }
        }

        var serviceIds = executionSettings is not null ? string.Join("|", executionSettings.Select(model => model.ServiceId).ToArray()) : null;
        var modelIds = executionSettings is not null ? string.Join("|", executionSettings.Select(model => model.ModelId).ToArray()) : null;
        var message = new StringBuilder($"Required service of type {typeof(T)} not registered.");
        if (!string.IsNullOrEmpty(serviceIds))
        {
            message.Append($" Expected serviceIds: {serviceIds}.");
        }
        if (!string.IsNullOrEmpty(modelIds))
        {
            message.Append($" Expected modelIds: {modelIds}.");
        }
        throw new KernelException(message.ToString());
    }

    private T? GetServiceByModelId<T>(Kernel kernel, string modelId) where T : class, IAIService
    {
        var services = kernel.GetAllServices<T>();
        foreach (var service in services)
        {
            string? serviceModelId = service.GetModelId();
            if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId == modelId)
            {
                return service;
            }
        }

        return default;
    }
}

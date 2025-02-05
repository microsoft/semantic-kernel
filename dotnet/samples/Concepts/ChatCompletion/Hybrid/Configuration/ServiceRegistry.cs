// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;

namespace ChatCompletion.Hybrid;

internal static class ServiceRegistry
{
    public static void RegisterServices(ServiceCollection serviceCollection, Stream configSource)
    {
        var json = JsonDocument.Parse(configSource);

        var servicesElement = json.RootElement.GetProperty("services");

        foreach (var serviceConfig in servicesElement.EnumerateArray())
        {
            var serviceType = Type.GetType(serviceConfig.GetProperty("type").GetString()!);
            var factoryType = Type.GetType(serviceConfig.GetProperty("factory").GetProperty("type").GetString()!);

            if (serviceType == null || factoryType == null)
            {
                throw new InvalidOperationException($"Unable to resolve type");
            }

            var lifetime = Enum.Parse<ServiceLifetime>(serviceConfig.GetProperty("lifetime").GetString()!, true);

            switch (lifetime)
            {
                case ServiceLifetime.Singleton:
                    serviceCollection.AddKeyedSingleton(serviceType, serviceConfig.GetProperty("serviceKey").GetString(), (serviceProvider, _) =>
                    {
                        JsonElement? config = null;

                        if (serviceConfig.GetProperty("factory").TryGetProperty("configuration", out JsonElement _config))
                        {
                            config = _config;
                        }

                        var factory = Activator.CreateInstance(factoryType, serviceProvider, config)!;

                        return factoryType.InvokeMember("Create", System.Reflection.BindingFlags.InvokeMethod, null, factory, null, CultureInfo.InvariantCulture)!;
                    });
                    break;
                case ServiceLifetime.Scoped:
                    /// TBD
                    break;
                case ServiceLifetime.Transient:
                    /// TBD
                    break;
                default:
                    throw new Exception("Unsupported lifetime.");
            }
        }
    }
}

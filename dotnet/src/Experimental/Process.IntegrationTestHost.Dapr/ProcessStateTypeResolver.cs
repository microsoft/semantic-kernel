// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// An implementation of <see cref="JsonTypeInfoResolver"/> that resolves the type information for <see cref="KernelProcessStepState{T}"/>.
/// </summary>
public class ProcessStateTypeResolver<T> : DefaultJsonTypeInfoResolver where T : KernelProcessStep
{
    private static readonly Type s_genericType = typeof(KernelProcessStep<>);
    private readonly Dictionary<string, Type> _types =
        new()
        {
            { "process", typeof(KernelProcessState) },
            { "map", typeof(KernelProcessMapState) },
        };

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStateTypeResolver{T}"/> class.
    /// </summary>
    public ProcessStateTypeResolver()
    {
        // Load all types from the resources assembly that derive from KernelProcessStep
        var assembly = typeof(T).Assembly;
        var stepTypes = assembly.GetTypes().Where(t => t.IsSubclassOf(typeof(KernelProcessStep)));

        foreach (var type in stepTypes)
        {
            if (TryGetSubtypeOfStatefulStep(type, out Type? genericStepType) && genericStepType is not null)
            {
                var userStateType = genericStepType.GetGenericArguments()[0];
                var stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
                this._types.TryAdd(userStateType.Name, stateType);
            }
        }
    }

    /// <inheritdoc />
    public override JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions options)
    {
        JsonTypeInfo jsonTypeInfo = base.GetTypeInfo(type, options);

        Type baseType = typeof(KernelProcessStepState);
        if (jsonTypeInfo.Type == baseType)
        {
            var jsonDerivedTypes = this._types.Select(t => new JsonDerivedType(t.Value, t.Key)).ToList();

            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions
            {
                TypeDiscriminatorPropertyName = "$state-type",
                IgnoreUnrecognizedTypeDiscriminators = true,
                UnknownDerivedTypeHandling = JsonUnknownDerivedTypeHandling.FailSerialization
            };

            // Add the known derived types to the collection
            var derivedTypesCollection = jsonTypeInfo.PolymorphismOptions.DerivedTypes;
            if (derivedTypesCollection is List<JsonDerivedType> list)
            {
                list.AddRange(jsonDerivedTypes);
            }
            else
            {
                foreach (var item in jsonDerivedTypes!)
                {
                    derivedTypesCollection!.Add(item);
                }
            }
        }
        else if (jsonTypeInfo.Type == typeof(DaprStepInfo))
        {
            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions
            {
                TypeDiscriminatorPropertyName = "$state-type",
                IgnoreUnrecognizedTypeDiscriminators = true,
                UnknownDerivedTypeHandling = JsonUnknownDerivedTypeHandling.FailSerialization,
                DerivedTypes =
                {
                    new JsonDerivedType(typeof(DaprProcessInfo), nameof(DaprProcessInfo)),
                    new JsonDerivedType(typeof(DaprMapInfo), nameof(DaprMapInfo)),
                    new JsonDerivedType(typeof(DaprProxyInfo), nameof(DaprProxyInfo)),
                }
            };
        }

        return jsonTypeInfo;
    }

    private static bool TryGetSubtypeOfStatefulStep(Type? type, out Type? genericStateType)
    {
        while (type != null && type != typeof(object))
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == s_genericType)
            {
                genericStateType = type;
                return true;
            }

            type = type.BaseType;
        }

        genericStateType = null;
        return false;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization.Metadata;
using System.Text.Json.Serialization;
using System.Text.Json;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of an individual step in a process.
/// </summary>
[DataContract]
[KnownType(nameof(GetKnownTypes))]
public record KernelProcessStepState
{
    /// <summary>
    /// A set of known types that may be used in serialization.
    /// </summary>
    internal readonly static HashSet<Type> s_knownTypes = [];

    /// <summary>
    /// Used to dynamically provide the set of known types for serialization.
    /// </summary>
    /// <returns></returns>
    private static HashSet<Type> GetKnownTypes() => s_knownTypes;

    /// <summary>
    /// Registers a derived type for serialization. Types registered here are used by the KnownType attribute
    /// to support DataContractSerialization of derived types as required to support Dapr.
    /// </summary>
    /// <param name="derivedType">A Type that derives from <typeref name="KernelProcessStepState"/></param>
    internal static void RegisterDerivedType(Type derivedType)
    {
        s_knownTypes.Add(derivedType);
    }

    /// <summary>
    /// The identifier of the Step which is required to be unique within an instance of a Process.
    /// This may be null until a process containing this step has been invoked.
    /// </summary>
    [DataMember]
    public string? Id { get; init; }

    /// <summary>
    /// The name of the Step. This is intended to be human readable and is not required to be unique. If
    /// not provided, the name will be derived from the steps .NET type.
    /// </summary>
    [DataMember]
    public string Name { get; init; }

    /// <summary>
    /// Used to dynamically provide the set of known types for serialization.
    /// </summary>
    /// <returns></returns>
    public static IJsonTypeInfoResolver JsonTypeInfoResolver => new ProcessStatePolymorphicTypeResolver();

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string? id = null)
    {
        Verify.NotNullOrWhiteSpace(name);

        this.Id = id;
        this.Name = name;
    }
}

/// <summary>
/// Represents the state of an individual step in a process that includes a user-defined state object.
/// </summary>
/// <typeparam name="TState">The type of the user-defined state.</typeparam>
[DataContract]
public sealed record KernelProcessStepState<TState> : KernelProcessStepState where TState : class, new()
{
    /// <summary>
    /// The user-defined state object associated with the Step.
    /// </summary>
    [DataMember]
    public TState? State { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string? id = null)
        : base(name, id)
    {
        Verify.NotNullOrWhiteSpace(name);

        this.Id = id;
        this.Name = name;
    }
}

/// <summary>
/// IJsonTypeInfoResolver implementation that provides polymorphic serialization support for <see cref="KernelProcessStepState"/>.
/// </summary>
public sealed class ProcessStatePolymorphicTypeResolver : DefaultJsonTypeInfoResolver
{
    /// <inheritdoc>
    public override JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions options)
    {
        JsonTypeInfo jsonTypeInfo = base.GetTypeInfo(type, options);

        Type baseType = typeof(KernelProcessStepState);
        if (jsonTypeInfo.Type == baseType)
        {
            var uniqueTypes = KernelProcessStepState.s_knownTypes;
            uniqueTypes.Add(typeof(KernelProcessState));
            var derivedTypes = new List<Type>(uniqueTypes.Distinct());
            var jsonDerivedTypes = derivedTypes.Select(t => new JsonDerivedType(t, t.Name)).ToList();

            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions
            {
                TypeDiscriminatorPropertyName = "$state-type",
                IgnoreUnrecognizedTypeDiscriminators = true,
                UnknownDerivedTypeHandling = JsonUnknownDerivedTypeHandling.FailSerialization
            };

            jsonTypeInfo.PolymorphismOptions.DerivedTypes.AddRange(jsonDerivedTypes);
        }

        return jsonTypeInfo;
    }
}

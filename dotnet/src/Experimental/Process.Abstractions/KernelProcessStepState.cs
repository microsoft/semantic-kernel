// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.Serialization;

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
    private static readonly ConcurrentDictionary<string, Type> s_knownTypes = [];

    /// <summary>
    /// Used to dynamically provide the set of known types for serialization.
    /// </summary>
    /// <returns></returns>
    private static IEnumerable<Type> GetKnownTypes() => s_knownTypes.Values;

    /// <summary>
    /// Registers a derived type for serialization. Types registered here are used by the KnownType attribute
    /// to support DataContractSerialization of derived types as required to support Dapr.
    /// </summary>
    /// <param name="derivedType">A Type that derives from <typeref name="KernelProcessStepState"/></param>
    internal static void RegisterDerivedType(Type derivedType)
    {
        s_knownTypes.TryAdd(derivedType.Name, derivedType);
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
    /// Version of the state
    /// </summary>
    [DataMember]
    public string Version { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="version">version id of the process step state</param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string version, string? id = null)
    {
        Verify.NotNullOrWhiteSpace(name, nameof(name));
        Verify.NotNullOrWhiteSpace(version, nameof(version));

        this.Id = id;
        this.Name = name;
        this.Version = version;
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
    /// <param name="version">version id of the process step state</param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string version, string? id = null)
        : base(name, version, id)
    {
        Verify.NotNullOrWhiteSpace(name);

        this.Id = id;
        this.Name = name;
        this.Version = version;
    }
}

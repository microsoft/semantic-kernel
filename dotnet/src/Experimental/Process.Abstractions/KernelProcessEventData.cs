// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Runtime.Serialization;
using System.Text.Json;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of an internal message used in a process runtime received by proxy steps.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessEventData"/> class.
/// </remarks>
[DataContract]
public sealed record KernelProcessEventData
{
    /// <summary>
    /// The assembly qualified name of the object type
    /// </summary>
    [DataMember]
    public string ObjectType { get; set; } = string.Empty;
    /// <summary>
    /// The Json serialized object
    /// </summary>
    [DataMember]
    public string Content { get; set; } = string.Empty;

    /// <summary>
    /// Converts serialized object to original object type
    /// </summary>
    /// <returns></returns>
    public object? ToObject()
    {
        Verify.NotNullOrWhiteSpace(this.ObjectType);
        Type? type = Type.GetType(this.ObjectType);
        if (type != null)
        {
            try
            {
                return JsonSerializer.Deserialize(this.Content, type);
            }
            catch (JsonException)
            {
                throw new KernelException($"Cannot deserialize object {this.Content}");
            }
        }

        return null;
    }

    /// <summary>
    /// Converts from original object to serialized version of the object
    /// </summary>
    /// <param name="obj">object to be serialized</param>
    /// <returns>instance of <see cref="KernelProcessEventData"/></returns>
    public static KernelProcessEventData? FromObject(object? obj)
    {
        if (obj == null)
        {
            return null;
        }

        Verify.NotNull(obj.GetType());
        Verify.NotNull(obj.GetType().AssemblyQualifiedName);

        try
        {
            return new KernelProcessEventData()
            {
                ObjectType = obj.GetType().AssemblyQualifiedName!,
                Content = JsonSerializer.Serialize(obj)
            };
        }
        catch (NotSupportedException)
        {
            throw new KernelException($"Cannot serialize object {obj.GetType().FullName}");
        }
    }
}

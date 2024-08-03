// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.Grpc.Model;

/// <summary>
/// The gRPC operation data contract field.
/// </summary>
internal sealed class GrpcOperationDataContractTypeFiled(string name, int number, string typeName)
{
    /// <summary>
    /// Field name.
    /// </summary>
    public string Name { get; } = name;

    /// <summary>
    /// Field number.
    /// </summary>
    public int Number { get; } = number;

    /// <summary>
    /// Field type name.
    /// </summary>
    public string TypeName { get; } = typeName;
}

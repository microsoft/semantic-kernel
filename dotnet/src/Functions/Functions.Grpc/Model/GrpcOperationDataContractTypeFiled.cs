// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Functions.Grpc.Model;

/// <summary>
/// The gRPC operation data contract field.
/// </summary>
internal class GrpcOperationDataContractTypeFiled
{
    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationDataContractTypeFiled"/> class.
    /// </summary>
    public GrpcOperationDataContractTypeFiled(string name, int number, string typeName)
    {
        this.Name = name;
        this.Number = number;
        this.TypeName = typeName;
    }

    /// <summary>
    /// Field name.
    /// </summary>
    public string Name { get; private set; }

    /// <summary>
    /// Field number.
    /// </summary>
    public int Number { get; private set; }

    /// <summary>
    /// Field type name.
    /// </summary>
    public string TypeName { get; private set; }
}

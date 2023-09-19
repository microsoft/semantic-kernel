// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Functions.Grpc.Model;

/// <summary>
/// The gRPC operation data contract.
/// </summary>
internal class GrpcOperationDataContractType
{
    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationDataContractType"/> class.
    /// </summary>
    public GrpcOperationDataContractType(string name, IList<GrpcOperationDataContractTypeFiled> fields)
    {
        this.Name = name;
        this.Fields = fields;
    }

    /// <summary>
    /// Data contract name
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// List of fields
    /// </summary>
    public IList<GrpcOperationDataContractTypeFiled> Fields { get; } = new List<GrpcOperationDataContractTypeFiled>();
}

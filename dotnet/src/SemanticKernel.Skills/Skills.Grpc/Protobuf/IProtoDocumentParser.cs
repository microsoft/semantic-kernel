using System.Collections.Generic;
using System.IO;
using Microsoft.SemanticKernel.Skills.Grpc.Model;

namespace Microsoft.SemanticKernel.Skills.Grpc.Protobuf;

/// <summary>
/// Interface for .proto document parser classes.
/// </summary>
internal interface IProtoDocumentParser
{
    /// <summary>
    /// Parses .proto document.
    /// </summary>
    /// <param name="document">The .proto document.</param>
    /// <param name="name">The .proto file logical name.</param>
    /// <returns>List of gRPC operations.</returns>
    IList<GrpcOperation> Parse(Stream document, string name);
}

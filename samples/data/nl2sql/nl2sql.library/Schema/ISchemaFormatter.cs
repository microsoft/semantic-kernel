// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System.IO;
using System.Threading.Tasks;

internal interface ISchemaFormatter
{
    Task WriteAsync(TextWriter writer, SchemaDefinition schema);
}

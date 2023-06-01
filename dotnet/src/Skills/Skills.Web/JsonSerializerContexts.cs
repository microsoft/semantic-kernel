// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Web.Bing;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(BingConnector.BingSearchResponse))]
[JsonSerializable(typeof(IEnumerable<string>))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}

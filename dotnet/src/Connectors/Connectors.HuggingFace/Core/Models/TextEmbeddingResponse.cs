// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// Represents the response from the Hugging Face text embedding API.
/// </summary>
/// <returns> List&lt;ReadOnlyMemory&lt;float&gt;&gt;</returns>
internal sealed class TextEmbeddingResponseType1 : List<ReadOnlyMemory<float>>;

/// <summary>
/// Represents the response from the Hugging Face text embedding API.
/// </summary>
/// <returns>List&lt;List&lt;List&lt;ReadOnlyMemory&lt;float&gt;&gt;&gt;&gt;</returns>
internal sealed class TextEmbeddingResponseType2 : List<List<List<ReadOnlyMemory<float>>>>;


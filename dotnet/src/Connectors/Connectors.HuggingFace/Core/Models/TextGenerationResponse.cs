// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class TextGenerationResponse : List<GeneratedTextItem>;

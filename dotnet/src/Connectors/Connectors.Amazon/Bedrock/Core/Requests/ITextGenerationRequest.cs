// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Connectors.Amazon.Core.Requests;

public interface ITextGenerationRequest
{
    string InputText { get; }

    double? TopP { get; }

    double? Temperature { get; }

    int? MaxTokens { get; }

    IList<string>? StopSequences { get; }
}

// Copyright (c) Microsoft. All rights reserved.

namespace Connectors.Amazon.Core.Requests;

public interface ITextGenerationRequest //essentially an InvokeModelRequest
{
    string InputText { get; }

    double? TopP { get; }

    double? Temperature { get; }

    int? MaxTokens { get; }

    IList<string>? StopSequences { get; }
}

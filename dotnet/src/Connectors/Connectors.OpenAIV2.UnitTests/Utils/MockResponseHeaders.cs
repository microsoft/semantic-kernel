// Copyright (c) Microsoft. All rights reserved.

/* Phase 01
This class was imported and adapted from the System.ClientModel Unit Tests.
https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/System.ClientModel/tests/TestFramework/Mocks/MockResponseHeaders.cs
*/

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;

namespace SemanticKernel.Connectors.OpenAI.UnitTests;

public class MockResponseHeaders : PipelineResponseHeaders
{
    private readonly Dictionary<string, string> _headers;

    public MockResponseHeaders()
    {
        this._headers = new Dictionary<string, string>();
    }

    public override IEnumerator<KeyValuePair<string, string>> GetEnumerator()
    {
        throw new NotImplementedException();
    }

    public override bool TryGetValue(string name, out string? value)
    {
        return this._headers.TryGetValue(name, out value);
    }

    public override bool TryGetValues(string name, out IEnumerable<string>? values)
    {
        throw new NotImplementedException();
    }
}

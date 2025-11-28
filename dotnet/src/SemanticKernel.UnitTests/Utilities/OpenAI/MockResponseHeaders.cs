// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;

namespace SemanticKernel.UnitTests.Utilities.OpenAI;

public class MockResponseHeaders : PipelineResponseHeaders
{
    private readonly Dictionary<string, string> _headers;

    public MockResponseHeaders()
    {
        this._headers = [];
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

// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public interface IStatementParser<T> where T : Statement
{
    T Parse(string input);
}

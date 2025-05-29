// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerConstants
{
    internal const string VectorStoreSystemName = "microsoft.sql_server";

    // The actual number is actually higher (2_100), but we want to avoid any kind of "off by one" errors.
    internal const int MaxParameterCount = 2_000;

    internal const int MaxIndexNameLength = 128;
}

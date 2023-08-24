// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal static class Symbols
{
    internal const char BlockStarter = '{';
    internal const char BlockEnder = '}';

    internal const char VarPrefix = '$';
    internal const char NamedArgBlockSeparator = '=';

    internal const char DblQuote = '"';
    internal const char SglQuote = '\'';
    internal const char EscapeChar = '\\';

    internal const char Space = ' ';
    internal const char Tab = '\t';
    internal const char NewLine = '\n';
    internal const char CarriageReturn = '\r';
}

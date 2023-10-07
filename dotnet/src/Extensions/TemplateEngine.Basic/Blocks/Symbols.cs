// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine.Basic.Blocks;

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

    internal static bool IsVarPrefix(char c)
    {
        return (c == Symbols.VarPrefix);
    }

    internal static bool IsBlankSpace(char c)
    {
        return c is Symbols.Space or Symbols.NewLine or Symbols.CarriageReturn or Symbols.Tab;
    }

    internal static bool IsQuote(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote;
    }

    internal static bool CanBeEscaped(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote or Symbols.EscapeChar;
    }
}

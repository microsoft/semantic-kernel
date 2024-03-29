// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Text;

/// <summary>Encodes message tags</summary>\
/// </remarks>
[ExcludeFromCodeCoverage]
internal static class MessageTagEncoder
{
    private const string MessagePattern = @"<message(\s+role=['""]\w+['""])?>(.*?)";

    private static string ReplaceMessageTag(Match match)
    {
        return match.Value.Replace("<", "&lt;").Replace(">", "&gt;"); ;
    }

    internal static string Encode(string value)
    {
        string result = Regex.Replace(value, MessagePattern, ReplaceMessageTag);
        result = result.Replace("</message>", "&lt;/message&gt;");
        return result;
    }

}

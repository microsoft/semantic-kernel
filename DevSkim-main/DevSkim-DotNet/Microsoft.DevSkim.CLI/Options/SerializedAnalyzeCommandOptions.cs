using System.Collections.Generic;

namespace Microsoft.DevSkim.CLI.Options;

/// <summary>
/// A serializable options object to provide to the analyze command.
/// </summary>
public record SerializedAnalyzeCommandOptions : BaseAnalyzeCommandOptions
{
    /// <summary>
    /// Dictionary that maps Language name to RuleIDs to ignore
    /// </summary>
    public IDictionary<string, List<string>> LanguageRuleIgnoreMap { get; set; } =
        new Dictionary<string, List<string>>();
}
namespace Microsoft.DevSkim.CLI;

public enum ExitCode
{
    Okay = 0,
    NoIssues = 0,
    IssuesExists = -1,
    CriticalError = -2,
    ArgumentParsingError = -3
}
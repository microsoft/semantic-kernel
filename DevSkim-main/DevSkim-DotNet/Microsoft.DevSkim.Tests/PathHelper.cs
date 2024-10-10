namespace Microsoft.DevSkim.Tests;

internal static class PathHelper
{
    /// <summary>
    /// Returns a randomly named temporary file, optionally with the extension provided.
    /// </summary>
    /// <param name="extension">The file extension to use, without '.'. For example, 'cs'</param>
    /// <returns>The a random file in the temporary directory. The file is not created.</returns>
    internal static string GetRandomTempFile(string? extension = null)
    {
        return extension switch
        {
            { } => Path.Combine(Path.GetTempPath(), $"{Path.GetRandomFileName()}.{extension}"),
            _ => Path.Combine(Path.GetTempPath(), Path.GetRandomFileName())
        };
    }
}
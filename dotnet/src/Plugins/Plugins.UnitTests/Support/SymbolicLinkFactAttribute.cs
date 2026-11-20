// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Runtime.InteropServices;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests;

[AttributeUsage(AttributeTargets.Method)]
internal sealed class SymbolicLinkFactAttribute : FactAttribute
{
    public SymbolicLinkFactAttribute()
    {
        this.Skip = SymbolicLinkTestSupport.SkipReason;
    }
}

[AttributeUsage(AttributeTargets.Method)]
internal sealed class SymbolicLinkTheoryAttribute : TheoryAttribute
{
    public SymbolicLinkTheoryAttribute()
    {
        this.Skip = SymbolicLinkTestSupport.SkipReason;
    }
}

[AttributeUsage(AttributeTargets.Method)]
internal sealed class UnixFactAttribute : FactAttribute
{
    public UnixFactAttribute()
    {
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Linux) &&
            !RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
        {
            this.Skip = "This test covers Unix special files.";
        }
    }
}

[AttributeUsage(AttributeTargets.Method)]
internal sealed class LinuxNonRootFactAttribute : FactAttribute
{
    public LinuxNonRootFactAttribute()
    {
        this.Skip = LinuxNonRootTestSupport.SkipReason;
    }
}

[AttributeUsage(AttributeTargets.Method)]
internal sealed class LinuxNonRootTheoryAttribute : TheoryAttribute
{
    public LinuxNonRootTheoryAttribute()
    {
        this.Skip = LinuxNonRootTestSupport.SkipReason;
    }
}

internal static class LinuxNonRootTestSupport
{
    internal static string? SkipReason { get; } =
        !RuntimeInformation.IsOSPlatform(OSPlatform.Linux)
            ? "This test requires Linux directory permissions."
            : GetEffectiveUserId() == 0
                ? "Root can bypass the directory permissions this test needs to enforce."
                : null;

    [DllImport("libc", EntryPoint = "geteuid")]
    private static extern uint GetEffectiveUserId();
}

internal static class SymbolicLinkTestSupport
{
    internal static string? SkipReason { get; } = GetSkipReason();

    private static string? GetSkipReason()
    {
        var directory = Path.Combine(Path.GetTempPath(), $"SymbolicLinkProbe_{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        try
        {
            File.CreateSymbolicLink(Path.Combine(directory, "file-link"), Path.Combine(directory, "target"));
            Directory.CreateSymbolicLink(Path.Combine(directory, "directory-link"), directory);
            return null;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            return $"Symbolic link creation is not permitted: {ex.Message}";
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }
}

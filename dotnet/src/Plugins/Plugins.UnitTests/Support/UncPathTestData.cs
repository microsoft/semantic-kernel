// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.Plugins.UnitTests;

public static class UncPathTestData
{
    public static TheoryData<string> Paths => new()
    {
        @"\\localhost\share\file.txt",
        "//localhost/share/file.txt",
        @"/\localhost\share\file.txt",
        @"\/localhost/share/file.txt",
        @"\\?\C:\folder\file.txt",
        "//?/C:/folder/file.txt",
        @"/\?\C:\folder\file.txt",
        @"\/?/C:/folder/file.txt",
        @"\\.\C:\folder\file.txt",
        "//./C:/folder/file.txt",
        @"/\.\C:\folder\file.txt",
        @"\/./C:/folder/file.txt",
        @"\\?\UNC\localhost\share\file.txt",
        "//?/UNC/localhost/share/file.txt",
        @"/\?\UNC\localhost\share\file.txt",
        @"\/?/UNC/localhost/share/file.txt",
        @"\??\UNC\localhost\share\file.txt",
        @"\??\C:\folder\file.txt",
        @"\\",
        "//",
        @"/\",
        @"\/",
        @"\??\"
    };
}

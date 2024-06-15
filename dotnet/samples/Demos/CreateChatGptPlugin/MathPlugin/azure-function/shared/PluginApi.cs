// Copyright (c) Microsoft. All rights reserved.

namespace skchatgptazurefunction.PluginShared;

/// <summary>
/// This class represents the plugin API specification.
/// </summary>
public class PluginApi
{
    /// <summary>
    /// The API specification
    /// </summary>
    public string Type { get; set; } = "openapi";

    /// <summary>
    /// URL used to fetch the specification
    /// </summary>
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string Url { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings
}

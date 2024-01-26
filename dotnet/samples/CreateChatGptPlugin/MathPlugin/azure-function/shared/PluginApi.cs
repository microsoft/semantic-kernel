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
    public string Url { get; set; } = string.Empty;
}

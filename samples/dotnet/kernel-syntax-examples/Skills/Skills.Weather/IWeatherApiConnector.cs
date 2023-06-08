// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Skills.Weather;

/// <summary>
/// Web search engine connector interface.
/// </summary>
public interface IWeatherApiConnector
{
    /// <summary>
    /// Execute a web request to a weather api.
    /// </summary>
    /// <param name="location">Location to get the weather for.</param>
    /// <param name="count">Number of results.</param>
    /// <param name="offset ">Number of results to skip.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>First snippet returned from search.</returns>
    Task<IEnumerable<string>> LookupWeatherAsync(string location, int count = 1, int offset = 0, CancellationToken cancellationToken = default);
}

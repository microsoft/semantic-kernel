// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010
#pragma warning disable CA2249 // Consider using 'string.Contains' instead of 'string.IndexOf'

namespace AIModelRouter;

/// <summary>
/// This class is for demonstration purposes only.
/// In a real-world scenario, you would use a more sophisticated routing mechanism, such as another local model for
/// deciding which service to use based on the user's input or any other criteria.
/// </summary>
internal sealed class CustomRouter()
{
    /// <summary>
    /// Returns the best service id to use based on the user's input.
    /// This demonstration uses a simple logic where your input is checked for specific keywords as a deciding factor,
    /// if no keyword is found it defaults to the first service in the list.
    /// </summary>
    /// <param name="lookupPrompt">User's input prompt</param>
    /// <param name="serviceIds">List of service ids to choose from in order of importance, defaulting to the first</param>
    /// <returns>Service id.</returns>
    internal string GetService(string lookupPrompt, List<string> serviceIds)
    {
        // The order matters, if the keyword is not found, the first one is used.
        foreach (var serviceId in serviceIds)
        {
            if (Contains(lookupPrompt, serviceId))
            {
                return serviceId;
            }
        }

        return serviceIds[0];
    }

    // Ensure compatibility with both netstandard2.0 and net8.0 by using IndexOf instead of Contains
    private static bool Contains(string prompt, string pattern)
        => prompt.IndexOf(pattern, StringComparison.CurrentCultureIgnoreCase) >= 0;
}

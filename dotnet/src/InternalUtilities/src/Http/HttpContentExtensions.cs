// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

internal static class HttpContentExtensions
{
    public static async Task<string> ReadAsStringAndTranslateExceptionAsync(this HttpContent httpContent)
    {
        try
        {
            return await httpContent.ReadAsStringAsync().ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(message: ex.Message, innerException: ex);
        }
    }
}

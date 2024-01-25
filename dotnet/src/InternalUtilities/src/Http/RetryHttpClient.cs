using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

public class RetryHttpClient
{
    private readonly HttpClient _httpClient;
    private readonly int _maxAttempts;

    public RetryHttpClient(HttpClient httpClient, int maxAttempts)
    {
        this._httpClient = httpClient;
        this._maxAttempts = maxAttempts;
    }

    public async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, HttpCompletionOption completionOption, CancellationToken cancellationToken)
    {
        HttpResponseMessage response = null;
        for (int attempt = 0; attempt < this._maxAttempts; attempt++)
        {
            response = await this._httpClient.SendAsync(request, completionOption, cancellationToken).ConfigureAwait(false);

            if (response.StatusCode != (HttpStatusCode)429)
            {
                return response;
            }

            var retryAfterValue = response.Headers.RetryAfter?.Delta?.TotalSeconds ?? 1;
            await Task.Delay(TimeSpan.FromSeconds(retryAfterValue), cancellationToken).ConfigureAwait(false);
        }

        return response;
    }
}



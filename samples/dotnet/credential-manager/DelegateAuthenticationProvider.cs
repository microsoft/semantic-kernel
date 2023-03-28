// Copyright (c) Microsoft. All rights reserved.

namespace CredentialManagerExample;

/// <summary>
/// Authenticate request async delegate.
/// </summary>
/// <param name="request">The <see cref="HttpRequestMessage"/> to authenticate.</param>
/// <returns></returns>
public delegate Task AuthenticateRequestAsyncDelegate(HttpRequestMessage request);

/// <summary>
/// A default <see cref="IAuthenticationProvider"/> implementation.
/// </summary>
public class DelegateAuthenticationProvider : IAuthenticationProvider
{
    /// <summary>
    /// Constructs an <see cref="DelegateAuthenticationProvider"/>.
    /// </summary>
    public DelegateAuthenticationProvider(AuthenticateRequestAsyncDelegate authenticateRequestAsyncDelegate)
    {
        this.AuthenticateRequestAsyncDelegate = authenticateRequestAsyncDelegate;
    }

    /// <summary>
    /// Gets or sets the delegate for authenticating requests.
    /// </summary>
    public AuthenticateRequestAsyncDelegate AuthenticateRequestAsyncDelegate { get; set; }

    /// <summary>
    /// Authenticates the specified request message.
    /// </summary>
    /// <param name="request">The <see cref="HttpRequestMessage"/> to authenticate.</param>
    public Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        if (this.AuthenticateRequestAsyncDelegate != null)
        {
            return this.AuthenticateRequestAsyncDelegate(request);
        }

        return Task.FromResult(0);
    }
}

//
// Summary:
//     Interface for authenticating requests.
public interface IAuthenticationProvider
{
    //
    // Summary:
    //     Authenticates the specified request message.
    //
    // Parameters:
    //   request:
    //     The System.Net.Http.HttpRequestMessage to authenticate.
    //
    // Returns:
    //     The task to await.
    Task AuthenticateRequestAsync(HttpRequestMessage request);
}

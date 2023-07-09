// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;

/// <summary>
/// Represents a singleton implementation of <see cref="HttpClientHandler"/> that is not disposable.
/// </summary>
internal sealed class NonDisposableHttpClientHandler : HttpClientHandler
{
    /// <summary>
    /// Private constructor to prevent direct instantiation of the class.
    /// </summary>
    private NonDisposableHttpClientHandler()
    {
        this.CheckCertificateRevocationList = true;
    }

    /// <summary>
    /// Gets the singleton instance of <see cref="NonDisposableHttpClientHandler"/>.
    /// </summary>
    public static NonDisposableHttpClientHandler Instance { get; } = new();

    /// <summary>
    /// Disposes the underlying resources held by the <see cref="NonDisposableHttpClientHandler"/>.
    /// This implementation does nothing to prevent unintended disposal, as it may affect all references.
    /// </summary>
    /// <param name="disposing">True if called from <see cref="Dispose"/>, false if called from a finalizer.</param>
#pragma warning disable CA2215 // Dispose methods should call base class dispose
    protected override void Dispose(bool disposing)
#pragma warning restore CA2215 // Dispose methods should call base class dispose
    {
        // Do nothing if called explicitly from Dispose, as it may unintentionally affect all references.
        // The base.Dispose(disposing) is not called to avoid invoking the disposal of HttpClientHandler resources.
        // This implementation assumes that the HttpClientHandler is being used as a singleton and should not be disposed directly.
    }
}

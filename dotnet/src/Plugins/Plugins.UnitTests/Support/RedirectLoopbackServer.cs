// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Plugins.UnitTests;

internal sealed class RedirectLoopbackServer : IAsyncDisposable
{
    private readonly TcpListener _listener;
    private readonly CancellationTokenSource _cancellationTokenSource = new();
    private readonly Task _serverTask;
    private readonly string _redirectTargetPath;
    private readonly string _targetContentType;
    private readonly byte[] _targetContent;
    private int _redirectTargetContacted;

    public RedirectLoopbackServer(string redirectTargetPath, string targetContentType, byte[] targetContent)
    {
        this._redirectTargetPath = redirectTargetPath.StartsWith("/", StringComparison.Ordinal) ? redirectTargetPath : $"/{redirectTargetPath}";
        this._targetContentType = targetContentType;
        this._targetContent = targetContent;

        this._listener = new TcpListener(IPAddress.Loopback, 0);
        this._listener.Start();
        var endpoint = (IPEndPoint)this._listener.LocalEndpoint;
        this.BaseUri = new Uri($"http://{endpoint.Address}:{endpoint.Port}/");
        this._serverTask = this.RunAsync();
    }

    public Uri BaseUri { get; }

    public bool RedirectTargetContacted => Volatile.Read(ref this._redirectTargetContacted) != 0;

    public async ValueTask DisposeAsync()
    {
        this._cancellationTokenSource.Cancel();
        this._listener.Stop();
        await this._serverTask.ConfigureAwait(false);
        this._cancellationTokenSource.Dispose();
    }

    private async Task RunAsync()
    {
        while (!this._cancellationTokenSource.IsCancellationRequested)
        {
            TcpClient client;
            try
            {
                client = await this._listener.AcceptTcpClientAsync(this._cancellationTokenSource.Token).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (ObjectDisposedException) when (this._cancellationTokenSource.IsCancellationRequested)
            {
                break;
            }
            catch (SocketException) when (this._cancellationTokenSource.IsCancellationRequested)
            {
                break;
            }

            using (client)
            {
                try
                {
                    await this.HandleRequestAsync(client, this._cancellationTokenSource.Token).ConfigureAwait(false);
                }
                catch (OperationCanceledException) when (this._cancellationTokenSource.IsCancellationRequested)
                {
                    break;
                }
                catch (ObjectDisposedException) when (this._cancellationTokenSource.IsCancellationRequested)
                {
                    break;
                }
                catch (IOException)
                {
                    // Ignore client disconnects / truncated requests to keep the test helper stable.
                }
                catch (SocketException) when (this._cancellationTokenSource.IsCancellationRequested)
                {
                    break;
                }
            }
        }
    }

    private async Task HandleRequestAsync(TcpClient client, CancellationToken cancellationToken)
    {
        var stream = client.GetStream();
        using var reader = new StreamReader(stream, Encoding.ASCII, detectEncodingFromByteOrderMarks: false, bufferSize: 1024, leaveOpen: true);
        var requestLine = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
        string? header;
        do
        {
            header = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
        }
        while (!string.IsNullOrEmpty(header));

        var requestTarget = requestLine?.Split(' ')[1];
        if (requestTarget == "/start")
        {
            var response = $"HTTP/1.1 302 Found\r\nLocation: {new Uri(this.BaseUri, this._redirectTargetPath.TrimStart('/'))}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
            await stream.WriteAsync(Encoding.ASCII.GetBytes(response), cancellationToken).ConfigureAwait(false);
            return;
        }

        Interlocked.Exchange(ref this._redirectTargetContacted, 1);
        var responseHeaders = $"HTTP/1.1 200 OK\r\nContent-Type: {this._targetContentType}\r\nContent-Length: {this._targetContent.Length}\r\nConnection: close\r\n\r\n";
        await stream.WriteAsync(Encoding.ASCII.GetBytes(responseHeaders), cancellationToken).ConfigureAwait(false);
        await stream.WriteAsync(this._targetContent, cancellationToken).ConfigureAwait(false);
    }
}

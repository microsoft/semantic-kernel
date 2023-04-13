// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using Microsoft.Extensions.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Reliability;

public class DefaultHttpRetryHandlerFactory : HttpMessageHandlerBuilder
{
    public DefaultHttpRetryHandlerFactory(HttpRetryConfig config, ILoggerFactory? logFactory = null)
    {
        this._log = logFactory?.CreateLogger<DefaultHttpRetryHandlerFactory>() ??
            NullLogger<DefaultHttpRetryHandlerFactory>.Instance;
        this._config = config;
        this.PrimaryHandler = this.Build();
    }

    public override HttpMessageHandler Build()
    {
        return new DefaultHttpRetryHandler(this._config, this._log)
        {
            InnerHandler = new HttpClientHandler() { CheckCertificateRevocationList = true }
        };
    }

    private readonly HttpRetryConfig? _config;
    private readonly ILogger<DefaultHttpRetryHandlerFactory> _log;

    #region Ignored overrides
    public override string Name { get; set; } = string.Empty;
    public override HttpMessageHandler PrimaryHandler { get; set; }
    public override IList<DelegatingHandler> AdditionalHandlers => new List<DelegatingHandler>();
    #endregion
}

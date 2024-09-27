using MediatR;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using OmniSharp.Extensions.LanguageServer.Protocol.Models;
using OmniSharp.Extensions.LanguageServer.Protocol.Server;
using OmniSharp.Extensions.LanguageServer.Protocol.Workspace;

namespace DevSkim.LanguageServer;

internal class DidChangeConfigurationHandler : DidChangeConfigurationHandlerBase
{
    private readonly ILogger<DidChangeConfigurationHandler> _logger;
    private readonly ILanguageServerConfiguration _configuration;

    /// <summary>
    /// Handle configuration changes from vscode
    /// </summary>
    /// <param name="logger"></param>
    /// <param name="configuration"></param>
    public DidChangeConfigurationHandler(ILogger<DidChangeConfigurationHandler> logger, ILanguageServerConfiguration configuration)
    {
        _logger = logger;
        _configuration = configuration;
    }

    public override async Task<Unit> Handle(DidChangeConfigurationParams request, CancellationToken cancellationToken)
    {
        _logger.LogDebug("DidChangeConfigurationHandler.cs: DidChangeConfigurationParams");
        ConfigHelpers.SetScannerSettings(
            (IConfiguration)await _configuration.GetConfiguration(new ConfigurationItem { Section = "MS-CST-E.vscode-devskim" })
        );
        return Unit.Value;
    }
}
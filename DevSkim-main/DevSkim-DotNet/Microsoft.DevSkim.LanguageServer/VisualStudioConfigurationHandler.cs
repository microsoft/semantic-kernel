// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using MediatR;
using Microsoft.DevSkim.LanguageProtoInterop;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using OmniSharp.Extensions.JsonRpc;

namespace DevSkim.LanguageServer
{
    [Method(DevSkimMessages.SetServerSettings, Direction.ClientToServer)]
    public record DevSkimSetLanguageServerSettingsParams : IRequest
    {
        public JToken? ScannerSettings;
    }

    /// <summary>
    /// Provides settings from the client to the server
    /// </summary>
    public class VisualStudioConfigurationHandler : IJsonRpcRequestHandler<DevSkimSetLanguageServerSettingsParams>
    {
        public VisualStudioConfigurationHandler()
        {
        }

        Task<Unit> IRequestHandler<DevSkimSetLanguageServerSettingsParams, Unit>.Handle(DevSkimSetLanguageServerSettingsParams request, CancellationToken cancellationToken)
        {
            PortableScannerSettings? settings = request.ScannerSettings?.ToObject<PortableScannerSettings>();
            if (settings is { } deNulledSettings)
            {
                StaticScannerSettings.UpdateWith(deNulledSettings);
            }
            return Unit.Task;
        }
    }
}
using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Utilities;
using StreamJsonRpc;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.Threading;
using Task = System.Threading.Tasks.Task;
using System.ComponentModel.Composition;
using Microsoft.Build.Framework.XamlTypes;
using Microsoft.DevSkim.VisualStudio.ProcessTracker;
using Microsoft.DevSkim.VisualStudio;

namespace Microsot.DevSkim.LanguageClient
{
    [ContentType("code")]
    [Export(typeof(ILanguageClient))]
    public class DevSkimLanguageClient : ILanguageClient, ILanguageClientCustomMessage2
    {
        [ImportingConstructor]
        public DevSkimLanguageClient(IProcessTracker processTracker)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            _manager = new VisualStudioSettingsManager(ServiceProvider.GlobalProvider, this);
            _processTracker = processTracker;
        }

        /// <summary>
        /// A reference to the Rpc connection between the client and server
        /// </summary>
        internal JsonRpc Rpc
        {
            get;
            set;
        }
        /// Pushes changed settings to the server
        public SettingsChangedNotifier SettingsNotifier { get; private set; }
        /// <inheritdoc/>
        public string Name => "DevSkim Visual Studio Extension";
        // This handles incoming messages to the language client about fixes
        public object CustomMessageTarget => new DevSkimFixMessageTarget();
        /// Detects changes in the client settings
        private readonly VisualStudioSettingsManager _manager;
        /// Keeps track of the started language server process and ensures that it is properly closed when the extension closes.
        private readonly IProcessTracker _processTracker;
        /// <inheritdoc/>
        public async Task<Connection> ActivateAsync(CancellationToken token)
        {
            await Task.Yield();
            ProcessStartInfo info = new ProcessStartInfo();
            info.FileName = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), "Server", @"Microsoft.DevSkim.LanguageServer.exe");
            info.RedirectStandardInput = true;
            info.RedirectStandardOutput = true;
            info.UseShellExecute = false;
            info.CreateNoWindow = true;

            Process process = new Process();
            process.StartInfo = info;

            if (process.Start())
            {
                _processTracker.AddProcess(process);
                return new Connection(process.StandardOutput.BaseStream, process.StandardInput.BaseStream);
            }
            return null;
        }
        /// <inheritdoc/>
        public event AsyncEventHandler<EventArgs> StartAsync;
        /// <inheritdoc/>
        public event AsyncEventHandler<EventArgs> StopAsync;
        /// <inheritdoc/>
        public async Task OnLoadedAsync()
        {
            if (StartAsync != null)
            {
                await StartAsync.InvokeAsync(this, EventArgs.Empty);
            }
        }
        /// <inheritdoc/>
        public async Task StopServerAsync()
        {
            if (StopAsync != null)
            {
                await StopAsync.InvokeAsync(this, EventArgs.Empty);
            }
        }

        /// <inheritdoc/>
        public Task AttachForCustomMessageAsync(JsonRpc rpc)
        {
            Rpc = rpc;
            SettingsNotifier = new SettingsChangedNotifier(Rpc);
            return Task.CompletedTask;
        }

        /// <inheritdoc/>
        public async Task OnServerInitializedAsync()
        {
            await _manager.UpdateAllSettingsAsync();
        }

        /// <inheritdoc/>
        public Task<InitializationFailureContext> OnServerInitializeFailedAsync(ILanguageClientInitializationInfo initializationState)
        {
            string message = "DevSkim Language Client failed to activate.";
            string exception = initializationState.InitializationException?.ToString() ?? string.Empty;
            message = $"{message}\n {exception}";

            InitializationFailureContext failureContext = new InitializationFailureContext()
            {
                FailureMessage = message,
            };

            return Task.FromResult(failureContext);
        }

        // Not used but required by Interface
        /// <inheritdoc/>
        public IEnumerable<string> ConfigurationSections => null;
        /// <inheritdoc/>
        public object InitializationOptions => null;
        /// <inheritdoc/>
        public IEnumerable<string> FilesToWatch => null;
        /// <inheritdoc/>
        public bool ShowNotificationOnInitializeFailed => true;

        // This handles modifying outgoing messages to the language server
        /// <inheritdoc/>
        object ILanguageClientCustomMessage2.MiddleLayer => null;
    }
}

using System.Collections.Immutable;
using System.Text;
using MediatR;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.DevSkim;
using Microsoft.DevSkim.LanguageProtoInterop;
using Microsoft.Extensions.Logging;
using OmniSharp.Extensions.LanguageServer.Protocol;
using OmniSharp.Extensions.LanguageServer.Protocol.Client.Capabilities;
using OmniSharp.Extensions.LanguageServer.Protocol.Document;
using OmniSharp.Extensions.LanguageServer.Protocol.Models;
using OmniSharp.Extensions.LanguageServer.Protocol.Server;
using OmniSharp.Extensions.LanguageServer.Protocol.Server.Capabilities;
using Range = OmniSharp.Extensions.LanguageServer.Protocol.Models.Range;


namespace DevSkim.LanguageServer
{
    internal class TextDocumentSyncHandler : TextDocumentSyncHandlerBase
    {
        private readonly ILogger<TextDocumentSyncHandler> _logger;
        private readonly ILanguageServerFacade _facade;
        private readonly TextDocumentSelector _documentSelector = TextDocumentSelector.ForLanguage(StaticScannerSettings.RuleProcessorOptions.Languages.GetNames());
        private DevSkimRuleProcessor _processor => StaticScannerSettings.Processor;

        public TextDocumentSyncHandler(ILogger<TextDocumentSyncHandler> logger, ILanguageServerFacade facade)
        {
            _facade = facade;
            _logger = logger;
        }

        public TextDocumentSyncKind Change { get; } = TextDocumentSyncKind.Full;

        private async Task<Unit> GenerateDiagnosticsForTextDocumentAsync(string text, int? version, DocumentUri uri)
        {
            if (string.IsNullOrEmpty(text))
            {
                _logger.LogDebug("\tNo content found");
                return Unit.Value;
            }

            string filename = uri.Path;
            if (StaticScannerSettings.IgnoreFiles.Any(x => x.IsMatch(filename)))
            {
                _logger.LogDebug($"\t{filename} was excluded due to matching IgnoreFiles setting");
                return Unit.Value;
            }
            // Diagnostics are sent a document at a time
            _logger.LogDebug($"\tProcessing document: {filename}");
            List<Issue> issues = await Task.Run(() => _processor.Analyze(text, filename).ToList());
            ImmutableArray<Diagnostic>.Builder diagnostics = ImmutableArray<Diagnostic>.Empty.ToBuilder();
            ImmutableArray<CodeFixMapping>.Builder codeFixes = ImmutableArray<CodeFixMapping>.Empty.ToBuilder();
            _logger.LogDebug($"\tAdding {issues.Count} issues to diagnostics");
            foreach (Issue issue in issues)
            {
                if (!issue.IsSuppressionInfo)
                {
                    Diagnostic diag = new Diagnostic()
                    {
                        Code = $"{ConfigHelpers.Section}: {issue.Rule.Id}",
                        Severity = DevSkimSeverityToDiagnositicSeverity(issue.Rule.Severity),
                        Message = $"{issue.Rule.Description ?? string.Empty}",
                        // DevSkim/Application Inspector line numbers are one-indexed, but column numbers are zero-indexed
                        // To get the diagnostic to appear on the correct line, we must subtract 1 from the line number
                        Range = new Range(issue.StartLocation.Line - 1, issue.StartLocation.Column, issue.EndLocation.Line - 1, issue.EndLocation.Column),
                        Source = "DevSkim Language Server"
                    };
                    diagnostics.Add(diag);
                    for (int i = 0; i < issue.Rule.Fixes?.Count; i++)
                    {
                        CodeFix fix = issue.Rule.Fixes[i];
                        var targetText = text.Substring(issue.Boundary.Index, issue.Boundary.Length);
                        if (fix.Replacement is not null && DevSkimRuleProcessor.IsFixable(targetText, fix))
                        {
                            string? potentialFix = DevSkimRuleProcessor.Fix(targetText, fix);
                            if (potentialFix is { })
                            {
                                codeFixes.Add(new CodeFixMapping(diag, potentialFix, uri.ToUri(), $"Replace with {potentialFix}", version, issue.Boundary.Index, issue.Boundary.Index + issue.Boundary.Length, false));
                            }
                        }
                    }
                    // Add suppression options
                    if (StaticScannerSettings.RuleProcessorOptions.EnableSuppressions)
                    {
                        // TODO: We should check if there is an existing, expired suppression to update, and if so the replacement range needs to include the old suppression
                        // TODO: Handle multiple suppressions on one line?
                        string proposedSuppression = DevSkimRuleProcessor.GenerateSuppressionByFileName(filename, issue.Rule.Id, StaticScannerSettings.SuppressionStyle == SuppressionStyle.Block, 0, StaticScannerSettings.ReviewerName, StaticScannerSettings.RuleProcessorOptions.Languages);
                        if (!string.IsNullOrEmpty(proposedSuppression))
                        {
                            codeFixes.Add(new CodeFixMapping(diag, $" {proposedSuppression}", uri.ToUri(), $"Suppress {issue.Rule.Id}", version, issue.Boundary.Index, issue.Boundary.Index + issue.Boundary.Length, true));

                            if (StaticScannerSettings.SuppressionDuration > -1)
                            {
                                DateTime expiration = DateTime.Now.AddDays(StaticScannerSettings.SuppressionDuration);
                                string proposedTimedSuppression = DevSkimRuleProcessor.GenerateSuppressionByFileName(filename, issue.Rule.Id, StaticScannerSettings.SuppressionStyle == SuppressionStyle.Block, StaticScannerSettings.SuppressionDuration, StaticScannerSettings.ReviewerName, StaticScannerSettings.RuleProcessorOptions.Languages);
                                if (!string.IsNullOrEmpty(proposedSuppression))
                                {
                                    codeFixes.Add(new CodeFixMapping(diag, $" {proposedTimedSuppression}", uri.ToUri(), $"Suppress {issue.Rule.Id} until {expiration.ToString("yyyy-MM-dd")}", version, issue.Boundary.Index, issue.Boundary.Index + issue.Boundary.Length, true));
                                }
                            }
                        }
                    }
                }
            }

            _logger.LogDebug("\tPublishing diagnostics...");
            _facade.TextDocument.PublishDiagnostics(new PublishDiagnosticsParams()
            {
                Diagnostics = new Container<Diagnostic>(diagnostics.ToArray()),
                Uri = uri,
                Version = version
            });
            _facade.TextDocument.SendNotification(DevSkimMessages.FileVersion, new MappingsVersion() { version = version, fileName = uri.ToUri() });
            foreach (var mapping in codeFixes)
            {
                _facade.TextDocument.SendNotification(DevSkimMessages.CodeFixMapping, mapping);
            }

            return Unit.Value;
        }

        private static DiagnosticSeverity DevSkimSeverityToDiagnositicSeverity(Severity ruleSeverity)
        {
            return ruleSeverity switch
            {
                Severity.Unspecified => DiagnosticSeverity.Hint,
                Severity.Critical => DiagnosticSeverity.Error,
                Severity.Important => DiagnosticSeverity.Error,
                Severity.Moderate => DiagnosticSeverity.Warning,
                Severity.BestPractice => DiagnosticSeverity.Hint,
                Severity.ManualReview => DiagnosticSeverity.Hint,
                _ => DiagnosticSeverity.Information
            };
        }

        public override async Task<Unit> Handle(DidChangeTextDocumentParams request, CancellationToken cancellationToken)
        {
            _logger.LogDebug("TextDocumentSyncHandler.cs: DidChangeTextDocumentParams");
            if (StaticScannerSettings.ScanOnChange)
            {
                TextDocumentContentChangeEvent? content = request.ContentChanges.FirstOrDefault();
                if (content is null)
                {
                    _logger.LogDebug("\tNo content found");
                    return Unit.Value;
                }
                return await GenerateDiagnosticsForTextDocumentAsync(content.Text, request.TextDocument.Version, request.TextDocument.Uri);
            }
            return Unit.Value;
        }

        public override async Task<Unit> Handle(DidOpenTextDocumentParams request, CancellationToken cancellationToken)
        {
            _logger.LogDebug("TextDocumentSyncHandler.cs: DidOpenTextDocumentParams");
            if (StaticScannerSettings.ScanOnOpen)
            {
                TextDocumentItem content = request.TextDocument;
                return await GenerateDiagnosticsForTextDocumentAsync(content.Text, content.Version, request.TextDocument.Uri);
            }
            return Unit.Value;
        }

        public override Task<Unit> Handle(DidCloseTextDocumentParams request, CancellationToken cancellationToken)
        {
            _logger.LogDebug("TextDocumentSyncHandler.cs: DidCloseTextDocumentParams");
            if (StaticScannerSettings.RemoveFindingsOnClose)
            {
                _facade.TextDocument.PublishDiagnostics(new PublishDiagnosticsParams()
                {
                    Diagnostics = new Container<Diagnostic>(),
                    Uri = request.TextDocument.Uri,
                    Version = null
                });
            }
            return Unit.Task;
        }

        public override async Task<Unit> Handle(DidSaveTextDocumentParams request, CancellationToken cancellationToken)
        {
            _logger.LogDebug("TextDocumentSyncHandler.cs: DidSaveTextDocumentParams");
            if (StaticScannerSettings.ScanOnSave)
            {
                if (request.Text is null)
                {
                    _logger.LogDebug("\tNo content found");
                    return Unit.Value;
                }
                return await GenerateDiagnosticsForTextDocumentAsync(request.Text, null, request.TextDocument.Uri);
            }
            return Unit.Value;
        }

        public override TextDocumentAttributes GetTextDocumentAttributes(DocumentUri uri)
        {
            if (StaticScannerSettings.RuleProcessorOptions.Languages.FromFileNameOut(uri.GetFileSystemPath(), out LanguageInfo Info))
            {
                return new TextDocumentAttributes(uri, Info.Name);
            }
            return new TextDocumentAttributes(uri, "unknown");
        }

        protected override TextDocumentSyncRegistrationOptions CreateRegistrationOptions(TextSynchronizationCapability capability, ClientCapabilities clientCapabilities) => new TextDocumentSyncRegistrationOptions()
        {
            DocumentSelector = _documentSelector,
            Change = Change,
            Save = new SaveOptions() { IncludeText = true }
        };
    }
}
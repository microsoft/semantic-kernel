// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using Microsoft.VisualStudio.Imaging.Interop;
using Microsoft.VisualStudio.Language.Intellisense;
using Microsoft.VisualStudio.Text;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;
namespace Microsoft.DevSkim.VisualStudio
{
    using Microsoft.DevSkim.LanguageProtoInterop;
    using System;
    using System.Collections.Generic;
    using System.Threading.Tasks;

    internal class DevSkimSuggestedAction: ISuggestedAction
    {
        public DevSkimSuggestedAction(SnapshotSpan span, CodeFixMapping mapping)
        {
            _span = span;
            _snapshot = span.Snapshot;
            _mapping = mapping;
            DisplayText = mapping.friendlyString;
        }

        public string DisplayText { get; }

        public bool HasActionSets
        {
            get
            {
                return false;
            }
        }

        public bool HasPreview
        {
            get
            {
                return false;
            }
        }

        public string IconAutomationText
        {
            get
            {
                return null;
            }
        }

        ImageMoniker ISuggestedAction.IconMoniker
        {
            get
            {
                return default(ImageMoniker);
            }
        }

        public string InputGestureText
        {
            get
            {
                return null;
            }
        }

        public void Dispose()
        {
        }

        public Task<IEnumerable<SuggestedActionSet>> GetActionSetsAsync(CancellationToken cancellationToken)
        {
            return Task.FromResult<IEnumerable<SuggestedActionSet>>(Array.Empty<SuggestedActionSet>());
        }

        public Task<object> GetPreviewAsync(CancellationToken cancellationToken)
        {
            ITextSnapshotLine line = _snapshot.GetLineFromPosition(_span.Start.Position);

            TextBlock textBlock = new TextBlock();
            textBlock.Padding = new Thickness(5);
            textBlock.Inlines.Add(new Run() { Text = _mapping.replacement, Foreground = new SolidColorBrush(Color.FromRgb(0x34, 0xAF, 0x00)) });
            return Task.FromResult<object>(textBlock);
        }

        public void Invoke(CancellationToken cancellationToken)
        {
            if (cancellationToken.IsCancellationRequested)
            {
                return;
            }
            if (!_mapping.isSuppression)
            {
                _span.Snapshot.TextBuffer.Replace(new Microsoft.VisualStudio.Text.Span(_mapping.matchStart, _mapping.matchEnd - _mapping.matchStart), _mapping.replacement);
            }
            else
            {
                ITextSnapshotLine line = _span.Snapshot.GetLineFromLineNumber(_mapping.diagnostic.Range.End.Line);
                _span.Snapshot.TextBuffer.Insert(line.End.Position, _mapping.replacement);
            }
        }

        public bool TryGetTelemetryId(out Guid telemetryId)
        {
            telemetryId = Guid.Empty;
            return false;
        }

        private readonly CodeFixMapping _mapping;
        private readonly ITextSnapshot _snapshot;
        private readonly SnapshotSpan _span;
    }
}
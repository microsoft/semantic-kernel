using System.Collections;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.DevSkim.LanguageProtoInterop
{
    using OmniSharp.Extensions.LanguageServer.Protocol.Models;
    using System;

    /// <summary>
    /// Holds a set of CodeFixMappings for a specific file path and version for that file
    /// </summary>
    public class MappingsVersion
    {
        public int? version;
        public Uri fileName;
    }

    public class CodeFixMapping : IEquatable<CodeFixMapping>
    {
        /// <summary>
        /// Reported version of the document the diagnostic applies to
        /// </summary>
        public int? version;

        /// <summary>
        /// The diagnostic to attach the fix to
        /// </summary>
        public Diagnostic diagnostic { get; }
        /// <summary>
        /// The replacement to make
        /// </summary>
        public string replacement { get; }
        /// <summary>
        /// The Filename this fix should apply to
        /// </summary>
        public Uri fileName { get; }
        /// <summary>
        /// The description for the CodeFix in the IDE
        /// </summary>
        public string friendlyString { get; }

        /// <summary>
        /// The absolute character index for the start (used by Visual Studio Extension)
        /// </summary>
        public int matchStart { get; }

        /// <summary>
        /// The absolute character index for the start (used by Visual Studio Extension)
        /// </summary>
        public int matchEnd { get; }

        /// <summary>
        /// The absolute character index for the start (used by Visual Studio Extension)
        /// </summary>
        public bool isSuppression { get; }

        /// <summary>
        /// Create a codefixmapping to send to the IDE
        /// </summary>
        /// <param name="diagnostic"></param>
        /// <param name="replacement"></param>
        /// <param name="fileName"></param>
        /// <param name="friendlyString"></param>
        public CodeFixMapping(Diagnostic diagnostic, string replacement, Uri fileName, string friendlyString, int? version, int matchStart, int matchEnd, bool isSuppression)
        {
            this.version = version;
            this.diagnostic = diagnostic;
            this.replacement = replacement;
            this.fileName = fileName;
            this.friendlyString = friendlyString;
            this.matchStart = matchStart;
            this.matchEnd = matchEnd;
            this.isSuppression = isSuppression;
        }

        public bool Equals(CodeFixMapping other)
        {
            if (ReferenceEquals(null, other)) return false;
            if (ReferenceEquals(this, other)) return true;
            return version == other.version && Equals(diagnostic, other.diagnostic) && replacement == other.replacement && Equals(fileName, other.fileName) && friendlyString == other.friendlyString && matchStart == other.matchStart && matchEnd == other.matchEnd && isSuppression == other.isSuppression;
        }

        public override bool Equals(object obj)
        {
            if (ReferenceEquals(null, obj)) return false;
            if (ReferenceEquals(this, obj)) return true;
            if (obj.GetType() != this.GetType()) return false;
            return Equals((CodeFixMapping)obj);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                var hashCode = version.GetHashCode();
                hashCode = (hashCode * 397) ^ (diagnostic != null ? diagnostic.GetHashCode() : 0);
                hashCode = (hashCode * 397) ^ (replacement != null ? replacement.GetHashCode() : 0);
                hashCode = (hashCode * 397) ^ (fileName != null ? fileName.GetHashCode() : 0);
                hashCode = (hashCode * 397) ^ (friendlyString != null ? friendlyString.GetHashCode() : 0);
                hashCode = (hashCode * 397) ^ matchStart;
                hashCode = (hashCode * 397) ^ matchEnd;
                hashCode = (hashCode * 397) ^ isSuppression.GetHashCode();
                return hashCode;
            }
        }
    }
}

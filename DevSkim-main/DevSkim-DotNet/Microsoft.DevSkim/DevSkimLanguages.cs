using System.IO;
using System.Reflection;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.Extensions.Logging;

namespace Microsoft.DevSkim
{
    public static class DevSkimLanguages
    {
        /// <summary>
        /// Create a languages object from embedded resources.
        /// </summary>
        /// <param name="loggerFactory"></param>
        /// <returns></returns>
        public static Languages LoadEmbedded(ILoggerFactory? loggerFactory = null)
        {
            Assembly assembly = Assembly.GetExecutingAssembly();
            Stream? languages = assembly
                .GetManifestResourceStream("Microsoft.DevSkim.resources.languages.json");
            Stream? comments = assembly
                .GetManifestResourceStream("Microsoft.DevSkim.resources.comments.json");
            return new Languages(null, comments, languages);
        }

        /// <summary>
        /// Create a Languages object from specified paths to comments and languages
        /// </summary>
        /// <param name="commentsPath"></param>
        /// <param name="languagesPath"></param>
        /// <returns></returns>
        public static Languages FromFiles(string commentsPath, string languagesPath)
        {
            Stream comments = File.OpenRead(commentsPath);
            Stream languages = File.OpenRead(languagesPath);
            return new Languages(null, comments, languages);
        }
    }
}


namespace Microsoft.DevSkim.VisualStudio.Options
{
    using Microsoft.VisualStudio.Shell;
    using System.Diagnostics.CodeAnalysis;
    using System.Runtime.InteropServices;

    /// <summary>
    /// This is the class that implements the package exposed by this assembly.
    /// </summary>
    [ProvideBindingPath]
    [Guid(PackageGuidString)]
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [InstalledProductRegistration("#110", "#112", "1.0", IconResourceID = 400)] // Info on this package for Help/About
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [ProvideOptionPage(typeof(GeneralOptionsPage), "DevSkim", "General", 1000, 1001, true)]
    [ProvideProfile(typeof(GeneralOptionsPage), "DevSkim", "General", 1000, 1002, true, DescriptionResourceID = 1003)]
    [SuppressMessage("StyleCop.CSharp.DocumentationRules", "SA1650:ElementDocumentationMustBeSpelledCorrectly", Justification = "pkgdef, VS and vsixmanifest are valid VS terms")]
    public sealed class OptionsPackage : AsyncPackage
    {
        /// <summary>
        /// OptionPackage GUID string.
        /// </summary>
        public const string PackageGuidString = "ef3feecc-7c99-42f5-aa32-95c3b0d389aa";

        /// <summary>
        /// Initializes a new instance of the <see cref="OptionsPackage"/> class.
        /// </summary>
        public OptionsPackage()
        {
            // Initialization code
        }

        #region Package Members

        #endregion
    }
}

export const Constants = {
    app: {
        name: 'Copilot',
        updateCheckIntervalSeconds: 60 * 5,
    },
    msal: {
        method: 'redirect', // 'redirect' | 'popup'
        auth: {
            clientId: process.env.REACT_APP_AAD_CLIENT_ID as string,
            authority: process.env.REACT_APP_AAD_AUTHORITY as string,
        },
        cache: {
            cacheLocation: 'localStorage',
            storeAuthStateInCookie: false,
        },
        skScopes: ['openid', 'offline_access', 'profile'],
    },
    bot: {
        profile: {
            id: 'bot',
            fullName: 'Copilot',
            emailAddress: '',
            photo: '/assets/bot-icon-1.png',
        },
        fileExtension: 'skcb',
        typingIndicatorTimeoutMs: 5000,
    },
    debug: {
        root: 'sk-chatbot',
    },
    sk: {
        service: {
            defaultDefinition: 'int',
        },
    },
    // This is not a comprehensive list, see https://learn.microsoft.com/en-us/graph/permissions-reference.
    // Uncomment the ones you need and pass into invokeSkillWithMsalToken (./connectors/useConnectors.ts)
    // Your application will need to be granted these permissions in Azure AD.
    msGraphScopes: [
        'Calendars.Read', // Get Schedule Availability
        // 'Calendars.ReadWrite',
        // 'Calendars.Read.Shared',
        // 'ChannelMessage.Read.All',
        // 'Chat.Read',
        // 'Contacts.Read',
        // 'Contacts.Read.Shared',
        // 'Files.Read',
        // 'Files.Read.All',
        // 'Files.Read.Selected',
        // 'Files.ReadWrite', // Upload Files to OneDrive, Create a Share link
        // 'Group.Read.All',
        'Mail.Read',
        // 'Mail.Read.Shared',
        // 'Mail.Send', // Send Email
        // 'MailboxSettings.Read',
        // 'Notes.Read',
        // 'Notes.Read.All',
        // 'offline_access',
        // 'OnlineMeetingArtifact.Read.All',
        // 'OnlineMeetings.Read',
        // 'OnlineMeetings.ReadWrite', // Create Meeting
        // 'OnlineMeetings.ReadWrite.All',
        // 'People.Read',
        // 'Presence.Read.All',
        // 'Sites.Read.All', // List Trending SharePoint Documents
        // 'Tasks.Read',
        // 'Tasks.Read.Shared',
        'Tasks.ReadWrite', // Manage Task or To Do Task list
        // 'TeamSettings.Read.All',
        'User.Read',
        // 'User.Read.All', // Get Manager (requires admin consent)
        // 'User.ReadBasic.All',
    ],
    adoScopes: ['vso.work'],
};

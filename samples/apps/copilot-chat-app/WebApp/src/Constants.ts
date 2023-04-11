export const Constants = {
    app: {
        name: 'SK Chatbot',
        updateCheckIntervalSeconds: 60 * 5,
    },
    msal: {
        method: 'redirect', // 'redirect' | 'popup'
        auth: {
            clientId: process.env.REACT_APP_AAD_CLIENT_ID as string,
            authority: `https://login.microsoftonline.com/common`,
        },
        cache: {
            cacheLocation: 'localStorage',
            storeAuthStateInCookie: false,
        },
        initialMsGraphScopes: ['openid', 'offline_access', 'profile', 'User.Read'],
    },
    bot: {
        profile: {
            id: 'bot',
            fullName: 'SK Chatbot',
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
    // NOT a comprehensize list.
    // Uncomment the ones you need and pass into
    // invokeSkillWithConnectorToken (./connectors/useConnectors.ts)
    msGraphScopes: [
        // 'Calendars.Read',
        // 'Calendars.ReadWrite',
        // 'Calendars.Read.Shared',
        // 'ChannelMessage.Read.All',
        // 'Chat.Read',
        // 'Contacts.Read',
        // 'Contacts.Read.Shared',
        // 'email',
        // 'Files.Read',
        // 'Files.Read.All',
        // 'Files.Read.Selected',
        // 'Group.Read.All',
        // 'Mail.Read',
        // 'Mail.Read.Shared',
        // 'MailboxSettings.Read',
        // 'Notes.Read',
        // 'Notes.Read.All',
        // 'offline_access',
        // 'OnlineMeetingArtifact.Read.All',
        // 'OnlineMeetings.Read',
        // 'OnlineMeetings.ReadWrite',
        // 'OnlineMeetings.ReadWrite.All',
        // 'People.Read',
        // 'Presence.Read.All',
        // 'Sites.Read.All',
        // 'Tasks.Read',
        // 'Tasks.Read.Shared',
        // 'Tasks.ReadWrite',
        // 'TeamSettings.Read.All',
        // 'User.Read.All',
        // 'User.ReadBasic.All',
    ],
    adoScopes: [
        // 'vso.work',
    ],
};

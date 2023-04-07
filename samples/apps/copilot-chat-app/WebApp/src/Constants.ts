export const Constants = {
    app: {
        name: 'SK Chatbot',
        updateCheckIntervalSeconds: 60 * 5,
    },
    msal: {
        method: 'redirect', // 'redirect' | 'popup'
        auth: {
            clientId: process.env.REACT_APP_CHAT_CLIENT_ID as string, 
            authority: `https://login.microsoftonline.com/common`,
        },
        cache: {
            cacheLocation: 'localStorage',
            storeAuthStateInCookie: false,
        },
        // Enable the ones you need
        msGraphScopes: [
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
            'openid',
            // 'People.Read',
            // 'Presence.Read.All',
            'offline_access',
            'profile',
            // 'Sites.Read.All',
            // 'Tasks.Read',
            // 'Tasks.Read.Shared',
            // 'TeamSettings.Read.All',
            'User.Read',
            // 'User.Read.all',
            // 'User.ReadBasic.All',
        ],
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
};

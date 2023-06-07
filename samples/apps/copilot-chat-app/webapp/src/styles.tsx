import { GriffelStyle, tokens } from '@fluentui/react-components';

export const CopilotChatTokens = {
    backgroundColor: '#9c2153',
    titleColor: '#943670',
};

export const Breakpoints = {
    small: (style: GriffelStyle): Record<string, GriffelStyle> => {
        return { '@media (max-width: 744px)': style };
    },
};

export const SharedStyles: Record<string, GriffelStyle> = {
    scroll: {
        overflowY: 'scroll',
        '&:hover': {
            '&::-webkit-scrollbar-thumb': {
                backgroundColor: tokens.colorScrollbarOverlay,
                visibility: 'visible',
            },
            '&::-webkit-scrollbar-track': {
                backgroundColor: tokens.colorNeutralBackground1,
                WebkitBoxShadow: 'inset 0 0 5px rgba(0, 0, 0, 0.1)',
                visibility: 'visible',
            },
        },
        height: '100%',
    },
};

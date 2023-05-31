import { GriffelStyle } from '@fluentui/react-components';

export const CopilotChatTokens = {
    backgroundColor: '#9c2153',
    titleColor: '#943670',
};

export const Breakpoints = {
    small: (style: GriffelStyle): Record<string, GriffelStyle> => {
        return { '@media (max-width: 744px)': style };
    },
};

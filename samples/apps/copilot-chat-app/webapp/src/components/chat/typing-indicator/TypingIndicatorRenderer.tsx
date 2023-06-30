// Copyright (c) Microsoft. All rights reserved.

import { makeStyles } from '@fluentui/react-components';
import { Animation } from '@fluentui/react-northstar';
import * as React from 'react';
import { TypingIndicator } from './TypingIndicator';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
    },
});

interface TypingIndicatorRendererProps {
    isBotTyping: boolean;
    numberOfUsersTyping: number;
}

export const TypingIndicatorRenderer: React.FC<TypingIndicatorRendererProps> = ({ isBotTyping, numberOfUsersTyping }) => {
    const classes = useClasses();

    let message = '';
    if (isBotTyping) {
        if (numberOfUsersTyping === 0) {
            message = 'Bot is typing';
        } else if (numberOfUsersTyping === 1) {
            message = 'Bot and 1 user are typing';
        } else {
            message = `Bot and ${numberOfUsersTyping} users are typing`;
        }
    } else if (numberOfUsersTyping === 1) {
        message = '1 user is typing';
    } else if (numberOfUsersTyping > 1) {
        message = `${numberOfUsersTyping} users are typing`;
    }

    if (!message) {
        return null;
    }

    const typingIndicator = (
        <div className={classes.root}>
            <label>{message}</label>
            <TypingIndicator />
        </div>
    );

    return <Animation name="slideInCubic" keyframeParams={{ distance: '2.4rem' }}>{typingIndicator}</Animation>;
};

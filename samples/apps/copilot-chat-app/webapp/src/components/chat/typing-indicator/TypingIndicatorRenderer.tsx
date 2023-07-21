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
    botResponseStatus: string | undefined;
    numberOfUsersTyping: number;
}

export const TypingIndicatorRenderer: React.FC<TypingIndicatorRendererProps> = ({
    botResponseStatus,
    numberOfUsersTyping,
}) => {
    const classes = useClasses();

    let message = botResponseStatus;
    if (numberOfUsersTyping === 1) {
        message = message ? `${message} and a user is typing` : 'A user is typing';
    } else if (numberOfUsersTyping > 1) {
        message = message
            ? `${message} and ${numberOfUsersTyping} users are typing`
            : `${numberOfUsersTyping} users are typing`;
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

    return (
        <Animation name="slideInCubic" keyframeParams={{ distance: '2.4rem' }}>
            {typingIndicator}
        </Animation>
    );
};

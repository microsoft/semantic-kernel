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

export const TypingIndicatorRenderer: React.FC<TypingIndicatorRendererProps> = (props) => {
    const { isBotTyping, numberOfUsersTyping } = props;
    const classes = useClasses();

    let message = "";
    if (isBotTyping && numberOfUsersTyping > 0) {
        if (numberOfUsersTyping === 1) {
            message = `Bot and ${numberOfUsersTyping} user are typing`;
        } else {
            message = `Bot and ${numberOfUsersTyping} users are typing`;
        }
    } else if (isBotTyping) {
        message = "Bot is typing";
    } else if (numberOfUsersTyping > 0) {
        if (numberOfUsersTyping === 1) {
            message = "1 user is typing";
        } else {
            message = `${numberOfUsersTyping} users are typing`;
        }
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

    return <Animation name="slideInCubic" keyframeParams={{ distance: '2.4rem' }} children={typingIndicator} />;
};

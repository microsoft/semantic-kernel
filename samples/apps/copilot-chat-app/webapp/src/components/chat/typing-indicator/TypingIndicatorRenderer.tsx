// Copyright (c) Microsoft. All rights reserved.

import { Persona, makeStyles } from '@fluentui/react-components';
import { Animation } from '@fluentui/react-northstar';
import * as React from 'react';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { TypingIndicator } from './TypingIndicator';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
    },
});

export const TypingIndicatorRenderer: React.FC = () => {
    // TODO: Make this stateless React component. No need to connect to app state.
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const classes = useClasses();

    const typingIndicator = (
        <div className={classes.root}>
            <Persona size="extra-small" avatar={{ image: { src: conversations[selectedId].botProfilePicture } }} />
            <TypingIndicator />
        </div>
    );

    return <Animation name="slideInCubic" keyframeParams={{ distance: '2.4rem' }} children={typingIndicator} />;
};

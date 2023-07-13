// Copyright (c) Microsoft. All rights reserved.

import { Image, makeStyles } from '@fluentui/react-components';
import React from 'react';
import typingBalls from '../../../assets/typing-balls-light.svg';

const useStyles = makeStyles({
    root: {
        contain: 'strict',
        height: '28px',
        overflowY: 'hidden',
        width: '28px',
    },
    image: {
        animationDuration: '2.3s',
        animationIterationCount: 'infinite',
        animationName: {
            from: { transform: 'translateY(0)' },
            // 28px Height * 68 Steps = 1904px
            to: { transform: 'translateY(-1904px)' },
        },
        animationTimingFunction: 'steps(68)',
    },
});

export const TypingIndicator: React.FC = () => {
    const classes = useStyles();

    return (
        <div className={classes.root}>
            <Image role="presentation" className={classes.image} src={typingBalls} />
        </div>
    );
};

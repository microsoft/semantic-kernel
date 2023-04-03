// Copyright (c) Microsoft. All rights reserved.

import { Button, Label, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    root: {
        height: '100%',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr',
        gridTemplateAreas: "'header' 'content'",
    },
    title: {
        ...shorthands.gridArea('title'),
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'row',
    },
    controls: {
        ...shorthands.gridArea('controls'),
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'row',
    },
    content: {
        ...shorthands.gridArea('content'),
        overflowY: 'auto',
    },
    contentOuter: {
        height: '100%',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
    },
    contentInner: {
        width: '100%',
    },
    restrictWidth: {
        maxWidth: '900px',
    },
});

interface PageViewerProps {
    title?: string;
    fillWidth?: boolean;
    onDismiss?: () => void;
    controlsLeft?: React.ReactNode;
    controlsRight?: React.ReactNode;
    children?: React.ReactNode;
}

export const PageViewer: React.FC<PageViewerProps> = (props) => {
    const { title, fillWidth, onDismiss, controlsLeft, controlsRight, children } = props;
    const classes = useClasses();

    const bodyClasses = fillWidth ? classes.contentInner : mergeClasses(classes.contentInner, classes.restrictWidth);

    return (
        <div className={classes.root}>
            <div className={classes.title}>
                {controlsLeft}
                {title && (
                    <Label size="large" weight="semibold">
                        {title}
                    </Label>
                )}
            </div>
            <div className={classes.controls}>
                {controlsRight}
                {onDismiss && <Button icon={<DismissRegular />} onClick={onDismiss} />}
            </div>
            <div className={classes.content}>
                <div className={classes.contentOuter}>
                    <div className={bodyClasses}>{children}</div>
                </div>
            </div>
        </div>
    );
};

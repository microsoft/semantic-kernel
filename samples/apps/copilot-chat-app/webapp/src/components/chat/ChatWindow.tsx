// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Label,
    makeStyles,
    mergeClasses,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    SelectTabEventHandler,
    shorthands,
    Tab,
    TabList,
    TabValue,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import { Alert } from '@fluentui/react-components/unstable';
import { Dismiss16Regular, Edit24Filled, EditRegular } from '@fluentui/react-icons';
import React, { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { removeAlert } from '../../redux/features/app/appSlice';
import { FeatureKeys } from '../../redux/features/app/AppState';
import { ChatResourceList } from './ChatResourceList';
import { ChatRoom } from './ChatRoom';
import { ParticipantsList } from './controls/ParticipantsList';
import { ShareBotMenu } from './controls/ShareBotMenu';
import { EditChatName } from './shared/EditChatName';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        backgroundColor: '#F5F5F5',
        boxShadow: 'rgb(0 0 0 / 25%) 0 0.2rem 0.4rem -0.075rem',
    },
    header: {
        ...shorthands.borderBottom('1px', 'solid', 'rgb(0 0 0 / 10%)'),
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
        backgroundColor: tokens.colorNeutralBackground4,
        display: 'flex',
        flexDirection: 'row',
        boxSizing: 'border-box',
        width: '100%',
        justifyContent: 'space-between',
    },
    title: {
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'row',
    },
    controls: {
        display: 'flex',
        alignItems: 'center',
    },
    popoverHeader: {
        ...shorthands.margin('0'),
        paddingBottom: tokens.spacingVerticalXXS,
        fontStyle: 'normal',
        fontWeight: '600',
    },
    popover: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        justifyContent: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXL),
        ...shorthands.gap(tokens.spacingVerticalMNudge),
        width: '398px',
    },
    input: {
        width: '100%',
    },
    alert: {
        ...shorthands.borderRadius(0),
    },
    infoAlert: {
        fontWeight: tokens.fontWeightRegular,
        color: tokens.colorNeutralForeground1,
        backgroundColor: tokens.colorNeutralBackground6,
        ...shorthands.borderRadius(0),
        fontSize: tokens.fontSizeBase200,
        lineHeight: tokens.lineHeightBase200,
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    buttons: {
        display: 'flex',
        alignSelf: 'end',
        ...shorthands.gap(tokens.spacingVerticalS),
    },
});

export const ChatWindow: React.FC = () => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { alerts, features } = useAppSelector((state: RootState) => state.app);

    const showShareBotMenu =
        !features[FeatureKeys.SimplifiedExperience].enabled &&
        (features[FeatureKeys.BotAsDocs].enabled || features[FeatureKeys.MultiUserChat].enabled);

    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chatName = conversations[selectedId].title;

    const [isEditing, setIsEditing] = useState<boolean>(false);

    const [selectedTab, setSelectedTab] = React.useState<TabValue>('chat');
    const onTabSelect: SelectTabEventHandler = (_event, data) => {
        setSelectedTab(data.value);
    };

    const onDismissAlert = (index: number) => {
        dispatch(removeAlert(index));
    };

    return (
        <div className={classes.root}>
            {alerts.map(({ type, message }, index) => {
                return (
                    <Alert
                        intent={type}
                        action={{
                            icon: (
                                <Dismiss16Regular
                                    aria-label="dismiss message"
                                    onClick={() => {
                                        onDismissAlert(index);
                                    }}
                                    color="black"
                                />
                            ),
                        }}
                        key={`${index}-${type}`}
                        className={mergeClasses(classes.alert, classes.infoAlert)}
                    >
                        {message}
                    </Alert>
                );
            })}
            <div className={classes.header}>
                <div className={classes.title}>
                    {!features[FeatureKeys.SimplifiedExperience].enabled && (
                        <>
                            <Persona
                                key={'Semantic Kernel Bot'}
                                size="medium"
                                avatar={{ image: { src: conversations[selectedId].botProfilePicture } }}
                                presence={{ status: 'available' }}
                            />
                            <Label size="large" weight="semibold">
                                {chatName}
                            </Label>
                            <Popover open={isEditing}>
                                <PopoverTrigger disableButtonEnhancement>
                                    <Tooltip content={'Edit conversation name'} relationship="label">
                                        <Button
                                            data-testid="editChatTitleButton"
                                            icon={isEditing ? <Edit24Filled /> : <EditRegular />}
                                            appearance="transparent"
                                            onClick={() => setIsEditing(true)}
                                            disabled={!chatName}
                                            aria-label="Edit conversation name"
                                        />
                                    </Tooltip>
                                </PopoverTrigger>
                                <PopoverSurface className={classes.popover}>
                                    <h3 className={classes.popoverHeader}>Bot name</h3>
                                    <EditChatName
                                        name={chatName}
                                        chatId={selectedId}
                                        exitEdits={() => setIsEditing(false)}
                                        textButtons
                                    />
                                </PopoverSurface>
                            </Popover>
                        </>
                    )}
                    <TabList selectedValue={selectedTab} onTabSelect={onTabSelect}>
                        <Tab data-testid="chatTab" id="chat" value="chat">
                            Chat
                        </Tab>
                        <Tab data-testid="filesTab" id="files" value="files">
                            Files
                        </Tab>
                    </TabList>
                </div>
                {!features[FeatureKeys.SimplifiedExperience].enabled && (
                    <div className={classes.controls}>
                        <div data-testid="chatParticipantsView">
                            <ParticipantsList participants={conversations[selectedId].users} />
                        </div>
                        {showShareBotMenu && (
                            <div>
                                <ShareBotMenu chatId={selectedId} chatTitle={chatName} />
                            </div>
                        )}
                    </div>
                )}
            </div>
            {selectedTab === 'chat' && <ChatRoom />}
            {selectedTab === 'files' && <ChatResourceList chatId={selectedId} />}
        </div>
    );
};

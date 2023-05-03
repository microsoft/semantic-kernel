// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { SKMultiUserChat } from './skMultiUserChat';

export const useSKMultiUserChat = (uri: string) => {
    const [skMultiUserChat] = React.useState(new SKMultiUserChat(uri));
    return skMultiUserChat;
};
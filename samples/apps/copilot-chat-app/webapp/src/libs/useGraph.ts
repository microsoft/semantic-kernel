import { useMsal } from '@azure/msal-react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { addAlert } from '../redux/features/app/appSlice';
import { UserData } from '../redux/features/users/UsersState';
import { setUsers } from '../redux/features/users/usersSlice';
import { TokenHelper } from './auth/TokenHelper';
import { AlertType } from './models/AlertType';
import { BatchRequest, BatchResponse, GraphService } from './services/GraphService';

export const useGraph = () => {
    const { instance, inProgress } = useMsal();
    const { users } = useAppSelector((state: RootState) => state.users);
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();
    const graphService = new GraphService();

    const loadUsers = async (userIds: string[]) => {
        const MAX_RETRIES = 3;
        let retries = 1;

        // Initialize empty arrays to store the results
        const loadedUsers: UserData[] = [];
        const usersToRetry: string[] = [];
        const failedUsers: string[] = [];
        const userData = { ...users };
        const usersToLoad: string[] = [];

        userIds.forEach((userId) => {
            const ids = userId.split('.');
            const oid = ids[0];
            const tid = ids[1];

            // Active user can only access user data within their own tenant
            // Mark chat users outside of tenant as External
            if (activeUserInfo && tid !== activeUserInfo.id.split('.')[1]) {
                userData[oid] = {
                    id: oid,
                    displayName: 'External User',
                };
            } else {
                // Only fetch users that haven't already been loaded
                if (!(oid in users)) {
                    usersToLoad.push(oid);
                }
            }
        });

        try {
            if (usersToLoad.length > 0) {
                await makeBatchGetUsersRequest(usersToLoad, loadedUsers, usersToRetry, failedUsers);

                while (usersToRetry.length > 0 && retries <= MAX_RETRIES) {
                    console.log(`Retrying batch request  ${retries}/${MAX_RETRIES}`);
                    await makeBatchGetUsersRequest(usersToRetry, loadedUsers, usersToRetry, failedUsers);
                    retries++;
                }

                loadedUsers.forEach((user) => {
                    userData[user.id] = user;
                });

                const unknownUsers = usersToRetry.concat(failedUsers);
                unknownUsers.forEach((userId) => {
                    userData[userId] = {
                        id: userId,
                        displayName: 'Unknown',
                    };
                });
            }

            dispatch(setUsers(userData));
        } catch (e: unknown) {
            dispatch(
                addAlert({
                    type: AlertType.Error,
                    message: e as string,
                }),
            );
        }
    };

    // Helper function to fetch user data in batches of 20
    const makeBatchGetUsersRequest = async (
        userIds: string[],
        loadedUsers: UserData[],
        usersToRetry: string[],
        failedUsers: string[],
    ) => {
        const getUserScope = 'User.Read';

        const token = await TokenHelper.getAccessTokenUsingMsal(inProgress, instance, [getUserScope]);

        // Loop through the user ids in chunks of the maximum batch size
        for (let i = 0; i < userIds.length; i += Constants.BATCH_REQUEST_LIMIT) {
            // Slice the current chunk of user ids
            const chunk = userIds.slice(i, i + Constants.BATCH_REQUEST_LIMIT);

            // Create an array of batch requests for the chunk
            const requests = chunk.map((id, index) => createGetUserRequest(id, i + index));

            // Send the batch request using Graph Service
            const responses: BatchResponse[] = await graphService.makeBatchRequest(requests, token);

            // Loop through the batch responses and parse the user data
            for (const response of responses) {
                const userData = parseGetUserResponse(response, userIds, usersToRetry, failedUsers);
                if (userData) {
                    // Push the user data to the results array
                    loadedUsers.push(userData);
                }
            }
        }
    };

    // Helper function to create a GetUser request given a user id
    const createGetUserRequest = (id: string, index: number): BatchRequest => {
        return {
            id: index.toString(),
            method: 'GET',
            url: `/users/${id}?$select=id,displayName,userPrincipalName`,
            headers: {
                'Content-Type': 'application/json',
            },
        };
    };

    // Helper function to extract the user data from a batch response
    const parseGetUserResponse = (
        response: BatchResponse,
        userIds: string[],
        usersToRetry: string[],
        failedUsers: string[],
    ): UserData | null => {
        if (response.status === 200 && response.body) {
            const user = response.body as UserData;
            return {
                id: user.id,
                displayName: user.displayName,
                userPrincipalName: user.userPrincipalName,
            };
        } else if (response.status >= 500) {
            // Transient error, try again
            usersToRetry.push(userIds[response.id]);
        } else {
            failedUsers.push(userIds[response.id]);
        }
        return null;
    };

    return {
        loadUsers,
    };
};

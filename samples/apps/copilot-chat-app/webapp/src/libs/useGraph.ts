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

        // Initialize empty arrays to store results
        const usersToLoad: string[] = [];
        const loadedUsers: UserData[] = [];
        const usersToRetry: string[] = [];

        try {
            // Copy current state of user data
            const userData = { ...users };

            // Filter user Ids list to optimize fetch
            userIds.forEach((userId) => {
                const ids = userId.split('.');
                const objectId = ids[0]; // Unique GUID assigned to each user in their home tenant
                const tenantId = ids[1]; // Home tenant id

                // Active user can only access user data within their own tenant
                // Mark chat users outside of tenant as External
                if (activeUserInfo && tenantId !== activeUserInfo.id.split('.')[1]) {
                    userData[objectId] = {
                        id: objectId,
                        displayName: 'External User',
                    };
                } else {
                    // Only fetch users that haven't already been loaded
                    if (!(objectId in users)) {
                        usersToLoad.push(objectId);
                    }
                }
            });

            if (usersToLoad.length > 0) {
                await makeBatchGetUsersRequest(usersToLoad, loadedUsers, usersToRetry);

                // Retry any users that failed with transient (5xx) errors up to 3 times
                while (usersToRetry.length > 0 && retries <= MAX_RETRIES) {
                    console.log(`Retrying batch request  ${retries}/${MAX_RETRIES}`);
                    await makeBatchGetUsersRequest(usersToRetry, loadedUsers, usersToRetry);
                    retries++;
                }

                // Populate user data record to update state
                loadedUsers.forEach((user) => {
                    userData[user.id] = user;
                });

                usersToRetry.forEach((userId) => {
                    userData[userId] = {
                        id: userId,
                        displayName: 'Unknown',
                    };
                });
            }

            dispatch(setUsers(userData));

            return userData;
        } catch (e: unknown) {
            dispatch(
                addAlert({
                    type: AlertType.Error,
                    message: e as string,
                }),
            );

            return;
        }
    };

    // Helper function to fetch user data in batches of up to 20
    const makeBatchGetUsersRequest = async (userIds: string[], loadedUsers: UserData[], usersToRetry: string[]) => {
        const getUserScope = 'User.ReadBasic.All';

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
                const userData = parseGetUserResponse(response, userIds, usersToRetry);
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
            // Failed to fetch, user data unavailable
            return {
                id: userIds[response.id],
                displayName: 'Unknown',
            };
        }
        return null;
    };

    return {
        loadUsers,
    };
};

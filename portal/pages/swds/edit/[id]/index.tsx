import React, { useContext, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useQuery, useQueryClient } from 'react-query';
import { ProfileForm } from '../../../../components/forms';
import { SET_SWDS_PROFILE, AppContext } from '../../../../contexts';
import useHttpClient from '../../../../hooks/useHttpClient';
import { ActionType, PERMISSIONS_TYPE } from '../../../../types';
import usePermission from '../../../../hooks/usePermission';

export default function EditProfile() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const isAllowed = usePermission();
  const { state, dispatch, status } = useContext(AppContext);

  useEffect(() => {
    if (
      status === 'ready' &&
      (!isAllowed(PERMISSIONS_TYPE.SWDS_UPDATE_PROFILE) || !isAllowed(PERMISSIONS_TYPE.SWDS_VIEW_PROFILE))
    ) {
      router.push(`/`);
    }
  }, [status, isAllowed, router]);

  const queryClient = useQueryClient();
  const { id, clone, editByImport } = router.query;
  const {
    isLoading,
    data: profileData,
    error: profileError,
  } = useQuery(['profilesData', id], () => httpClient.get(`/api/profiles?id=${id}`), { keepPreviousData: true });

  const updateProfile = async (data: any) => {
    const response = await httpClient.patch(`/api/profiles/${id}`, data);
    console.log('updateProfile', response);
    queryClient.setQueryData(['profilesData', id], response);
    router.push('/swds');
  };

  const updateProfileByImport = async (profilePath: string, data: any) => {
    try {
      const formData = new FormData();
      formData.append(data.name, data, data.name);
      const response = await httpClient.put(
        `/api/effective-profile/xml?path=${profilePath}`,
        formData,
        {
          'content-type': 'multipart/form-data',
        },
        true
      );
      return response;
    } catch (error) {
      console.log('updateProfileByImport error', error);
      throw error;
    }
  };

  const createCloneProfile = async (data: any) => {
    const response = await httpClient.post('/api/profiles', data);
    console.log('createCloneProfile', response);
    router.push('/swds');
    return response;
  };

  useEffect(() => {
    if (profileData) {
      dispatch({ type: SET_SWDS_PROFILE, payload: profileData });
    }
  }, [profileData, dispatch]);

  return (
    <>
      {isLoading || (!profileData && !profileError) ? (
        <div>Loading Profile ...</div>
      ) : profileError ? (
        <div>An error has occurred for loading Profile</div>
      ) : parseInt(clone as string) === 1 ? (
        <ProfileForm
          title={'Clone Profile'}
          profileData={profileData}
          apiHandler={createCloneProfile}
          actionType={ActionType.CLONE}
        />
      ) : parseInt(editByImport as string) === 1 ? (
        <ProfileForm
          title={'Update Profile from XML'}
          profileData={profileData}
          apiHandler={updateProfileByImport}
          actionType={ActionType.EDIT_BY_IMPORT}
        />
      ) : (
        <ProfileForm
          title={'Edit Profile'}
          profileData={profileData}
          apiHandler={updateProfile}
          actionType={ActionType.EDIT}
        />
      )}
    </>
  );
}

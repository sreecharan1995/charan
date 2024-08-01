import React, { useContext, useEffect } from 'react';
import { ProfileForm } from '../../../components';
import useHttpClient from '../../../hooks/useHttpClient';
import { ActionType, PERMISSIONS_TYPE } from '../../../types';
import { useRouter } from 'next/router';
import usePermission from '../../../hooks/usePermission';
import { AppContext } from '../../../contexts';

export default function CreateProfile() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const isAllowed = usePermission();
  const { status } = useContext(AppContext);

  useEffect(() => {
    if (status === 'ready' && !isAllowed(PERMISSIONS_TYPE.SWDS_CREATE_PROFILE)) {
      router.push(`/`);
    }
  }, [status, isAllowed, router]);

  const createProfile = async (data: any) => {
    const response = await httpClient.post('/api/profiles', data);
    console.log('createProfile', response);
    return response;
  };

  return <ProfileForm title={'Create New Profile'} apiHandler={createProfile} actionType={ActionType.CREATE} />;
}

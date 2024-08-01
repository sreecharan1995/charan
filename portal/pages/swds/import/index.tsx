import React, { useContext, useEffect } from 'react';
import { ProfileForm } from '../../../components';
import useHttpClient from '../../../hooks/useHttpClient';
import usePermission from '../../../hooks/usePermission';
import { ActionType, PERMISSIONS_TYPE } from '../../../types';
import { useRouter } from 'next/router';
import { AppContext } from '../../../contexts';

export default function ImportProfile() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const isAllowed = usePermission();
  const { status } = useContext(AppContext);

  useEffect(() => {
    if (status === 'ready' && !isAllowed(PERMISSIONS_TYPE.SWDS_CREATE_PROFILE)) {
      router.push(`/`);
    }
  }, [status, isAllowed, router]);

  const importProfile = async (profilePath: string, data: any) => {
    try {
      const formData = new FormData();
      formData.append(data.name, data, data.name);
      const response = await httpClient.post(
        `/api/effective-profile/xml?path=${profilePath}`,
        formData,
        {
          'content-type': 'multipart/form-data',
        },
        true
      );
      return response;
    } catch (error) {
      console.log('importProfile error', error);
      throw error;
    }
  };

  return <ProfileForm title={'Import Profile'} apiHandler={importProfile} actionType={ActionType.IMPORT} />;
}

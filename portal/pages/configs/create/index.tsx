import React, { useContext, useEffect } from 'react';
import { ConfigForm } from '../../../components/forms';
import { ActionType, PERMISSIONS_TYPE } from '../../../types';
import useHttpClient from '../../../hooks/useHttpClient';
import usePermission from '../../../hooks/usePermission';
import { AppContext } from '../../../contexts';
import { useRouter } from 'next/router';

export default function CreateConfiguration() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const isAllowed = usePermission();
  const { status } = useContext(AppContext);

  useEffect(() => {
    if (status === 'ready' && !isAllowed(PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG)) {
      router.push(`/`);
    }
  }, [status, isAllowed, router]);

  const createConfig = async (data: any) => {
    const response = await httpClient.post('/api/configs', data);
    console.log('createConfig', response);
    return response;
  };

  return <ConfigForm title={'Create New Configuration'} apiHandler={createConfig} actionType={ActionType.CREATE} />;
}

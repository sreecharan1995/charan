import React, { useContext, useEffect } from 'react';
import { ConfigForm } from '../../../../components/forms';
import { ActionType, PERMISSIONS_TYPE } from '../../../../types';
import { useRouter } from 'next/router';
import useHttpClient from '../../../../hooks/useHttpClient';
import { useQuery, useQueryClient } from 'react-query';
import { AppContext, SET_SWDS_PROFILE } from '../../../../contexts';
import usePermission from '../../../../hooks/usePermission';

export default function EditConfiguration() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const isAllowed = usePermission();
  const { state, dispatch, status } = useContext(AppContext);

  useEffect(() => {
    if (
      status === 'ready' &&
      (!isAllowed(PERMISSIONS_TYPE.CONFIGS_UPDATE_CONFIG) || !isAllowed(PERMISSIONS_TYPE.CONFIG_VIEW_CONFIG))
    ) {
      router.push(`/`);
    }
  }, [status, isAllowed, router]);

  const queryClient = useQueryClient();
  const { id, clone } = router.query;
  const {
    isLoading,
    data: configData,
    error: configError,
  } = useQuery(['configData', id], () => httpClient.get(`/api/configs/${id}`), { keepPreviousData: true });

  const updateConfig = async (data: any) => {
    const response = await httpClient.patch(`/api/configs/${id}`, data);
    console.log('updateConfig', response);
    queryClient.setQueryData(['configData', id], response);
    router.push('/configs');
  };

  const createCloneConfig = async (data: any) => {};

  useEffect(() => {
    if (configData) {
      dispatch({ type: SET_SWDS_PROFILE, payload: configData });
    }
  }, [configData, dispatch]);

  return (
    <>
      {isLoading || (!configData && !configError) ? (
        <div>Loading Config ...</div>
      ) : configError ? (
        <div>An error has occurred for loading Config</div>
      ) : clone ? (
        <ConfigForm
          title={'Clone Configuration'}
          configData={configData}
          apiHandler={createCloneConfig}
          actionType={ActionType.CLONE}
        />
      ) : (
        <ConfigForm
          title={'Edit Configuration'}
          configData={configData}
          apiHandler={updateConfig}
          actionType={ActionType.EDIT}
        />
      )}
    </>
  );
}

import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { useRouter } from 'next/router';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import LoadingButton from '@mui/lab/LoadingButton';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  FormInput,
  FormSwitch,
  FormTextArea,
  SiteLevelTreeView,
} from '../';
import { ActionType, PERMISSIONS_TYPE } from '../../types';
import Box from '@mui/material/Box';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { object, string } from 'yup';
import dynamic from 'next/dynamic';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { calculateDiffWithMaps, CREATE, DELETE, UPDATE } from './calculateDiff';
const SvelteJSONEditor = dynamic(
  () => import('../SvelteJSONEditor'),
  { ssr: false } // <-- not including this component on server-side
);

import useHttpClient from '../../hooks/useHttpClient';
import Restricted from '../controls/Restricted';

async function fetchConfigs(httpClient: any, q: string = '', path: string = '', p: number = 1, ps: number = 1000) {
  return httpClient.get(`/api/configs?p=${p}&ps=${ps}&name=${q}&path=${path}`);
}

async function updateConfigStatus(httpClient: any, id: any, data: any) {
  const response = await httpClient.put(`/api/configs/${id}/status`, { current: data });
  console.log('updateConfigStatus', response);
  return response;
}

type ContentType = {
  text?: string;
  json?: object;
};

export function ConfigForm(props: any) {
  const { title, configData, apiHandler, actionType } = props;
  const permission =
    actionType === ActionType.CREATE ? PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG : PERMISSIONS_TYPE.CONFIGS_UPDATE_CONFIG;
  const router = useRouter();
  const httpClient = useHttpClient();
  const [loading, setLoading] = useState(false);

  const [submitSuccess, setSubmitSuccess] = useState({ isSuccess: false, message: '' });
  const [submitError, setSubmitError] = useState({ open: false, message: null });
  const [configPath, setConfigPath] = useState<string>('');
  const [levelNode, setLevelNode] = useState<any>();
  const [inherits, setInherits] = useState<boolean>(false);

  // -------------------- //
  // JSON Editor
  const [configListVersions, setConfigListVersions] = useState<[]>([]);
  const [configVersionSelected, setConfigVersionSelected] = useState('');
  const [leftEditorContent, setLeftEditorContent] = useState<ContentType>(
    actionType === ActionType.EDIT
      ? {
          json: configData?.configuration,
        }
      : { text: '', json: undefined }
  );
  const [rightEditorContent, setRightEditorContent] = useState<ContentType>({ text: '', json: undefined });
  const {
    status,
    data: configVersionsData,
    error: configVersionsError,
    isFetching,
  } = useQuery(['configVersionsData'], () => fetchConfigs(httpClient, configData.name, configData.path), {
    keepPreviousData: true,
    enabled: !!configData,
  });

  const {
    isLoading,
    data: configVersionSelectedData,
    error: configVersionSelectedError,
  } = useQuery(
    ['configVersionSelectedData', configVersionSelected],
    () => {
      return httpClient.get(`/api/configs?id=${configVersionSelected}`);
    },
    { keepPreviousData: true, enabled: !!configVersionSelected }
  );

  const [diff, setDiff] = React.useState({});
  const handleDifferences = () => {
    const difference = calculateDiffWithMaps(leftEditorContent, rightEditorContent);
    setDiff(difference);
    console.log('difference->', difference);
    const diff_and_right = difference && difference.diffRight;
    const diff_and_left = difference && difference.diffLeft;
    console.log('***diff_and_right', diff_and_right);
    console.log('***diff_and_left', diff_and_left);
  };

  const onConfigVersionSelect = (event: SelectChangeEvent) => {
    setConfigVersionSelected(event.target.value);
  };

  useEffect(() => {
    if (configVersionsData && configVersionsData.items && configVersionsData.items.length > 0) {
      const data = configVersionsData.items
        .map((config: any) => {
          return {
            id: config.id,
            name: `${config.name} @ ${config.path} (${config.current ? 'Active' : 'Inactive'}) on ${config.updated}`,
          };
        })
        .filter((value: any, index: number) => {
          return value.id !== configData?.id;
        });
      setConfigListVersions(data);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configVersionsData]);

  useEffect(() => {
    if (configVersionSelectedData) {
      setRightEditorContent({ json: configVersionSelectedData.configuration });
    }
  }, [configVersionSelectedData]);
  // End JSON Editor
  // -------------------- //

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    setSubmitSuccess({ isSuccess: false, message: '' });
    setSubmitError({ open: false, message: null });
  };
  const handleCloseWithRedirect = (event?: React.SyntheticEvent | Event, reason?: string) => {
    handleClose(event, reason);
    router.push('/configs');
  };

  const schema =
    actionType === ActionType.CREATE
      ? object().shape({
          name: string().required('Configuration name is required'),
          description: string().required('Configuration description is required'),
        })
      : object().shape({});

  const {
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
  });

  const { mutate: apiMutate } = useMutation(apiHandler, {
    onSuccess: (data: any) => {
      console.log('useMutation ApiHandler onSuccess', data);
      setSubmitSuccess({ isSuccess: true, message: '' });
      reset();
      if (actionType === ActionType.CREATE) {
        router.push(`/configs`);
      }
    },
    onError: (error: any) => {
      console.log('useMutation ApiHandler onError', error);
      setSubmitError({
        open: true,
        message: Array.isArray(error?.response?.data?.message)
          ? JSON.stringify(error?.response?.data?.message)
          : error?.response?.data?.message || error?.message,
      });
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  const hasError = (data: any) => {
    if (!data || data.length <= 0) {
      return true;
    }
    return false;
  };

  const onSubmit = async (data: any) => {
    setLoading(true);
    data.configuration = leftEditorContent.text ? JSON.parse(leftEditorContent.text) : { ...leftEditorContent.json };

    try {
      if (configData && configData.current) {
        await updateConfigStatus(httpClient, configData.id, false);
        router.reload();
      } else if (actionType === ActionType.EDIT) {
        await updateConfigStatus(httpClient, configData.id, data.current);
        if (configPath && configPath.length > 0 && configPath !== configData.path) {
          data.level = {
            site: levelNode?.site,
            division: levelNode?.division,
            show: levelNode?.show,
            sequence_type: levelNode?.sequence_type,
            sequence: levelNode?.sequence,
            shot: levelNode?.shot,
          };
        }
        apiMutate({ ...data });
      } else {
        data.level = {
          site: levelNode?.site,
          division: levelNode?.division,
          show: levelNode?.show,
          sequence_type: levelNode?.sequence_type,
          sequence: levelNode?.sequence,
          shot: levelNode?.shot,
        };
        apiMutate({ ...data });
      }
    } catch (error) {
      setSubmitError({
        open: true,
        message: Array.isArray(error?.response?.data?.message)
          ? JSON.stringify(error?.response?.data?.message)
          : error?.response?.data?.message || error?.message,
      });
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (actionType === ActionType.CLONE) {
      configData.name = undefined;
      reset({ ...configData });
    } else {
      reset({ ...configData });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configData]);

  return (
    <>
      <Grid item xs={12}>
        <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
          {title}
        </Typography>
      </Grid>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Box
            sx={{
              maxWidth: '100%',
            }}
          >
            <FormInput
              control={control}
              name={'name'}
              id={'name'}
              label={'Enter Configuration Name (Example: default)'}
              error={errors.name}
              disabled={configData?.current}
            />
          </Box>
        </Grid>
        <Grid item xs={12}>
          <FormTextArea
            control={control}
            name={'description'}
            ariaLabel={'Enter Configuration Description'}
            placeholder={'Enter Configuration Description'}
            minRows={4}
            style={{ width: '100%' }}
            error={errors.description}
            disabled={configData?.current}
          />
        </Grid>
        <Grid item xs={12}>
          <Accordion defaultExpanded={true}>
            <AccordionSummary aria-controls="levels-accordion" id="levels-accordion">
              <Typography>Levels</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <SiteLevelTreeView
                disabled={configData?.current}
                onNodeSelect={setConfigPath}
                onLevelNode={setLevelNode}
                defaultSelected={
                  actionType === ActionType.EDIT || actionType === ActionType.CLONE ? configData.path : ''
                }
              ></SiteLevelTreeView>
            </AccordionDetails>
          </Accordion>
        </Grid>
        {actionType === ActionType.EDIT ? (
          <Grid item xs={12}>
            <Grid container justifyContent="end" alignItems="end">
              <FormControl sx={{ minWidth: 240 }} error={hasError(configVersionSelected)}>
                <InputLabel id="configVersion-label">Choose Versions:</InputLabel>
                <Select
                  labelId="configVersion-label"
                  id="configVersion-id"
                  label="Choose Versions:"
                  value={configVersionSelected}
                  onChange={onConfigVersionSelect}
                  disabled={configData?.current}
                >
                  {configListVersions.map((menuItem: any) => {
                    return (
                      <MenuItem key={menuItem.id} value={menuItem.id}>
                        {menuItem.name}
                      </MenuItem>
                    );
                  })}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        ) : null}
        <Grid item xs={12}>
          <Grid container direction="row" spacing={2}>
            <Grid item xs={6}>
              <div className="svelte-jsoneditor-react">
                <SvelteJSONEditor
                  content={leftEditorContent}
                  readOnly={configData?.current}
                  onChange={setLeftEditorContent}
                />
              </div>
            </Grid>
            {actionType === ActionType.EDIT ? (
              <>
                {/*<Grid item xs={2}>*/}
                {/*  <Grid container justifyContent="center" alignItems="center">*/}
                {/*    <Button variant="contained" size="large" onClick={() => handleDifferences()}>*/}
                {/*      Differences*/}
                {/*    </Button>*/}
                {/*  </Grid>*/}
                {/*</Grid>*/}
                <Grid item xs={6}>
                  <div className="svelte-jsoneditor-react">
                    <SvelteJSONEditor content={rightEditorContent} readOnly={true} onChange={setRightEditorContent} />
                  </div>
                </Grid>
              </>
            ) : null}
          </Grid>
        </Grid>
        <Grid item xs={12}>
          <FormSwitch control={control} name={'inherits'} label="Inherits" disabled={configData?.current} />
        </Grid>
        <Restricted to={PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG}>
          <Grid item xs={12}>
            <FormSwitch control={control} name={'current'} label="Active" disabled={configData?.current} />
          </Grid>
        </Restricted>
        <Grid item xs={12}>
          <Grid container direction="row" spacing={3} justifyContent="center" alignItems="center">
            <Grid item>
              <Button variant="contained" size="large" onClick={() => handleCloseWithRedirect()}>
                Cancel
              </Button>
            </Grid>
            <Grid item>
              <Restricted to={permission}>
                {configData?.current ? (
                  <LoadingButton
                    disabled={!configData?.current}
                    loading={loading}
                    variant="contained"
                    size="large"
                    onClick={handleSubmit(onSubmit)}
                  >
                    Deactivate
                  </LoadingButton>
                ) : (
                  <LoadingButton
                    disabled={configData?.current}
                    loading={loading}
                    variant="contained"
                    size="large"
                    onClick={handleSubmit(onSubmit)}
                  >
                    Save
                  </LoadingButton>
                )}
              </Restricted>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
      <Snackbar
        open={submitSuccess.isSuccess || submitError.open}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        {submitSuccess.isSuccess ? (
          <Alert onClose={handleClose} severity="success" sx={{ width: '100%' }}>
            {actionType === ActionType.CREATE || actionType === ActionType.CLONE
              ? 'Configuration has been successfully created!'
              : actionType === ActionType.IMPORT
              ? 'Configuration has been successfully imported!'
              : 'Configuration has been edited successfully!'}
          </Alert>
        ) : submitError.open ? (
          <Alert onClose={handleClose} severity="error" sx={{ width: '100%' }}>
            {actionType === ActionType.IMPORT
              ? 'Error importing configuration: ' + submitError.message
              : actionType === ActionType.CREATE || actionType === ActionType.CLONE
              ? submitError.message
                ? 'Error creating configuration: ' + submitError.message
                : 'Error creating configuration...'
              : submitError.message
              ? 'Error editing configuration: ' + submitError.message
              : 'Error editing configuration...'}
          </Alert>
        ) : undefined}
      </Snackbar>
    </>
  );
}

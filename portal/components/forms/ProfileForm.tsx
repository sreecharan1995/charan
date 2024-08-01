import React from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { useRouter } from 'next/router';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { object, string } from 'yup';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import LoadingButton from '@mui/lab/LoadingButton';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { Autocomplete } from '@mui/material';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  BundleModal,
  ConfirmDialog,
  FormInput,
  FormTextArea,
  SiteLevelTreeView,
  Table,
} from '../';
import CommentsList from '../CommentsList';
import Restricted from '../controls/Restricted';
import usePermission from '../../hooks/usePermission';
import { ActionType, PERMISSIONS_TYPE } from '../../types';
import useHttpClient from '../../hooks/useHttpClient';
import ImportResults from '../swds/ImportResults';

interface Bundle {
  id: string;
  name: string;
  description: string;
  status: string;
  packages: [];
}

interface RowData {
  id: string;
  name: string;
  description: string;
  status: string;
  packageItems: string;
  packages: [];
}

interface Column {
  id: 'name' | 'description' | 'status' | 'packageItems' | 'actions';
  label: string;
  minWidth?: number;
  align?: 'right';
  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: 'name', label: 'Name', minWidth: 100 },
  { id: 'description', label: 'Description', minWidth: 200 },
  {
    id: 'status',
    label: 'Status',
    minWidth: 100,
  },
  {
    id: 'packageItems',
    label: 'Packages',
    minWidth: 100,
  },
  {
    id: 'actions',
    label: '',
    minWidth: 100,
  },
];

function createRows(bundles: Bundle[]): RowData[] {
  let rows: RowData[] = [];
  if (Array.isArray(bundles)) {
    for (const b of bundles) {
      const bundle: Bundle = b;
      rows.push({
        ...bundle,
        packageItems: `${bundle.packages.length} items`,
        packages: bundle.packages,
      });
    }
  }
  return rows;
}

async function deleteProfileBundle(httpClient: any, id: string, bundleName: string) {
  const response = await httpClient.delete(`/api/profiles/${id}/bundles/${bundleName}`);
  console.log('deleteProfileBundle', response);
  return 'Profile bundle deleted successfully';
}

export function ProfileForm(props: any) {
  const { title, profileData, apiHandler, actionType } = props;
  const permission =
    actionType === ActionType.CREATE ? PERMISSIONS_TYPE.SWDS_CREATE_PROFILE : PERMISSIONS_TYPE.SWDS_UPDATE_PROFILE;
  const isAllowed = usePermission();
  const router = useRouter();
  const queryClient = useQueryClient();
  const httpClient = useHttpClient();
  const [loading, setLoading] = React.useState(false);

  const defaultProfilePath =
    actionType === ActionType.EDIT || actionType === ActionType.EDIT_BY_IMPORT || actionType === ActionType.CLONE
      ? profileData.path
      : '/';

  const [submitSuccess, setSubmitSuccess] = React.useState({ isSuccess: false, message: '' });
  const [submitError, setSubmitError] = React.useState({ open: false, message: null });
  const [profilePath, setProfilePath] = React.useState<string>(defaultProfilePath);

  // bundles
  const [p, setPage] = React.useState(1);
  const [ps, setPageSize] = React.useState(10);
  const [selectedBundles, setSelectedBundles] = React.useState<string[]>([]);
  const [bundleSearchValue, setBundleSearchValue] = React.useState<any[]>([]);
  const [openModal, setOpenModal] = React.useState<boolean>(false);
  const [bundleActionType, setBundleActionType] = React.useState<ActionType>(ActionType.CREATE);
  const [cloneBundle, setCloneBundle] = React.useState<RowData>();
  const [selectedRow, setSelectedRow] = React.useState<RowData>();
  const [openDialog, setOpenDialog] = React.useState(false);

  const [q, setSearchQuery] = React.useState('');
  const [xmlFile, setXmlFile] = React.useState<File>();

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    setSubmitSuccess({ isSuccess: false, message: '' });
    setSubmitError({ open: false, message: null });
  };
  const handleCloseWithRedirect = (event?: React.SyntheticEvent | Event, reason?: string) => {
    handleClose(event, reason);
    router.push('/swds');
  };

  const schema =
    actionType === ActionType.CREATE
      ? object().shape({
          name: string().required('Profile Name is required'),
          // status: string().required('Status is required'),
          description: string().required('Description is required'),
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
        router.push(`/swds/edit/${data.id}`);
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

  const onSubmit = async (data: any) => {
    setLoading(true);
    if (actionType === ActionType.IMPORT || actionType === ActionType.EDIT_BY_IMPORT) {
      try {
        const response = await apiHandler(profilePath, xmlFile);
        setSubmitSuccess({ isSuccess: true, message: response });
        setXmlFile(undefined);
        setProfilePath('');
      } catch (error: any) {
        setSubmitError({ open: true, message: error?.response?.data?.message || error?.message });
      } finally {
        setLoading(false);
      }
    } else {
      apiMutate({ ...data, path: profilePath || profileData?.path });
    }
  };

  const {
    isLoading: profileBundlesIsLoading,
    error: profileBundlesError,
    data: profileBundles,
  } = useQuery(
    ['profileBundles', p, ps, q],
    () => httpClient.get(`/api/profiles/${profileData.id}/bundles?p=${p}&ps=${ps}&q=${q}`),
    { enabled: !!profileData }
  );

  // Prefetch the next page!
  React.useEffect(() => {
    if (profileBundles?.navigation?.next) {
      queryClient.prefetchQuery(['profileBundles', p + 1, ps, q], () => {
        if (profileData && profileData.id) {
          return httpClient.get(`/api/profiles/${profileData.id}/bundles?p=${p}&ps=${ps}&q=${q}`);
        }
      });
    }
  }, [profileBundles, p, ps, q, queryClient, profileData, httpClient]);

  const handleChangePage = (newPage: number) => {
    setPage(newPage);
  };

  const handleChangePageSize = (pageSize: number) => {
    setPageSize(pageSize);
  };

  const {
    isLoading: listBundlesIsLoading,
    error: listBundlesError,
    data: listBundles,
  } = useQuery('listBundles', () => httpClient.get(`/api/bundles?p=${1}&ps=${100}&q=${q}`), {
    enabled: actionType === ActionType.EDIT || actionType === ActionType.CLONE,
  });

  const {
    isLoading: listEffectiveBundlesIsLoading,
    error: listEffectiveBundlesError,
    data: listEffectiveBundles,
  } = useQuery(
    ['listEffectiveBundles', profilePath],
    () => httpClient.get(`/api/effective-profile?path=${profilePath}`),
    {
      enabled:
        actionType === ActionType.CREATE ||
        actionType === ActionType.IMPORT ||
        actionType === ActionType.EDIT_BY_IMPORT,
    }
  );

  const postProfileBundle = async (bundles: any) => {
    if (profileData && profileData.id && Array.isArray(bundles)) {
      for (const bundle of bundles) {
        const response = await httpClient.post(`/api/profiles/${profileData.id}/bundles/${bundle}`);
        console.log('add existing bundle to profile', response);
      }
    }
  };

  const { mutate: profileBundleMutate } = useMutation(postProfileBundle, {
    onSuccess: async (data) => {
      console.log('useMutation profileBundle onSuccess', data);
      await queryClient.invalidateQueries('profileBundles');
      setSubmitSuccess({ isSuccess: true, message: '' });
      reset();
    },
    onError: (error: any) => {
      console.log('useMutation profileBundle onError', error);
      setSubmitError({ open: true, message: error?.response?.data?.message || error?.message });
    },
    onSettled: () => {},
  });

  const addProfileBundles = () => {
    profileBundleMutate(selectedBundles);
    setBundleSearchValue([]);
  };

  const fileImportHandler = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      console.log('file is', event.target.files[0]);
      setXmlFile(event.target.files[0]);
    }
  };

  const dialogConfirmAction = async () => {
    if (selectedRow) {
      try {
        const response = await deleteProfileBundle(httpClient, profileData.id, selectedRow.name);
        setSelectedRow(undefined);
        setSubmitSuccess({ isSuccess: true, message: response });
        await queryClient.invalidateQueries('profileBundles');
      } catch (error) {
        setSubmitError({ open: true, message: error?.message });
      }
    }
  };

  const handleTableBundleRowActions = (action: string, row: any) => {
    if (action === ActionType.CLONE) {
      setOpenModal(true);
      setCloneBundle(row);
      setBundleActionType(ActionType.CLONE);
    }
    if (action === ActionType.DELETE) {
      setSelectedRow(row);
      setOpenDialog(true);
    }
  };

  React.useEffect(() => {
    if (actionType === ActionType.CLONE) {
      profileData.name = undefined;
      reset({ ...profileData });
    } else {
      reset({ ...profileData });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileData]);

  return (
    <>
      {(actionType === ActionType.IMPORT || actionType === ActionType.EDIT_BY_IMPORT) && submitSuccess.isSuccess ? (
        <ImportResults data={submitSuccess.message} />
      ) : (
        <>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
                {title}
              </Typography>
            </Grid>
            {actionType !== ActionType.IMPORT && actionType !== ActionType.EDIT_BY_IMPORT ? (
              <>
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
                      label={'Enter Profile Name (Example: default)'}
                      error={errors.name}
                      disabled={!isAllowed(permission)}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <FormTextArea
                    control={control}
                    name={'description'}
                    ariaLabel={'Enter Profile Description'}
                    placeholder={'Enter Profile Description'}
                    minRows={4}
                    style={{ width: '100%' }}
                    error={errors.description}
                    disabled={!isAllowed(permission)}
                  />
                </Grid>
              </>
            ) : null}
            {actionType === ActionType.IMPORT || actionType === ActionType.EDIT_BY_IMPORT ? (
              <Grid item xs={12}>
                <Button variant="contained" component="label">
                  Upload XML
                  <input type="file" hidden onChange={fileImportHandler} />
                </Button>
              </Grid>
            ) : null}
            <Grid item xs={12}>
              <Accordion defaultExpanded={true}>
                <AccordionSummary aria-controls="levels-accordion" id="levels-accordion">
                  <Typography>Levels</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <SiteLevelTreeView
                    disabled={!isAllowed(permission)}
                    onNodeSelect={setProfilePath}
                    defaultSelected={defaultProfilePath}
                  ></SiteLevelTreeView>
                </AccordionDetails>
              </Accordion>
              {actionType === ActionType.CREATE ||
              actionType === ActionType.IMPORT ||
              actionType === ActionType.EDIT_BY_IMPORT ? (
                <Accordion defaultExpanded={true}>
                  <AccordionSummary aria-controls="bundles-accordion" id="bundles-accordion">
                    <Typography>Bundles</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={3}>
                      <Grid item xs={12}>
                        {listEffectiveBundlesIsLoading || !listEffectiveBundles ? (
                          <div>Loading Bundles ...</div>
                        ) : listEffectiveBundlesError ? (
                          <div>An error has occurred for loading Bundles</div>
                        ) : (
                          <Table
                            columns={columns}
                            rows={createRows(listEffectiveBundles.bundles)}
                            total={profileBundles?.navigation?.total}
                            page={p}
                            pageSize={1000}
                            pageChangeHandler={handleChangePage}
                            pageSizeChangeHandler={handleChangePageSize}
                            tableRowActionHandler={handleTableBundleRowActions}
                            disabled={true}
                            disabledPagination={true}
                          />
                        )}
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ) : null}
              {actionType === ActionType.EDIT || actionType === ActionType.CLONE ? (
                <>
                  <Accordion defaultExpanded={true}>
                    <AccordionSummary aria-controls="bundles-accordion" id="bundles-accordion">
                      <Typography>Bundles</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <Grid container spacing={2} alignItems="center">
                            <Grid item xs={11}>
                              {listBundlesIsLoading || !listBundles ? (
                                <div>Loading Bundles ...</div>
                              ) : listBundlesError ? (
                                <div>An error has occurred for loading Bundles</div>
                              ) : (
                                <Autocomplete
                                  disabled={!isAllowed(permission)}
                                  value={bundleSearchValue}
                                  multiple
                                  id="list-bundles"
                                  freeSolo
                                  getOptionLabel={(option: any) => option.name}
                                  options={listBundles.items}
                                  onChange={(event, newValue) => {
                                    setBundleSearchValue(newValue);
                                    if (Array.isArray(selectedBundles) && Array.isArray(newValue)) {
                                      const bundles = newValue.map((bundle) => bundle.name);
                                      setSelectedBundles(bundles);
                                    }
                                  }}
                                  renderInput={(params) => (
                                    <TextField {...params} label="Search bundle by name (Example: maya)" />
                                  )}
                                />
                              )}
                            </Grid>
                            <Grid item>
                              <Button
                                disabled={!isAllowed(permission)}
                                variant="contained"
                                size="large"
                                onClick={() => addProfileBundles()}
                              >
                                Add
                              </Button>
                            </Grid>
                          </Grid>
                        </Grid>
                        <Grid item xs={12}>
                          {profileBundlesIsLoading || !profileBundles ? (
                            <div>Loading Bundles ...</div>
                          ) : profileBundlesError ? (
                            <div>An error has occurred for loading Bundles</div>
                          ) : (
                            <Table
                              columns={columns}
                              rows={createRows(profileBundles.items)}
                              actions={['Clone', 'Delete']}
                              permissions={[PERMISSIONS_TYPE.SWDS_CREATE_BUNDLE, PERMISSIONS_TYPE.SWDS_DELETE_BUNDLE]}
                              total={profileBundles?.navigation?.total}
                              page={p}
                              pageSize={ps}
                              pageChangeHandler={handleChangePage}
                              pageSizeChangeHandler={handleChangePageSize}
                              tableRowActionHandler={handleTableBundleRowActions}
                              disabled={!isAllowed(permission)}
                            />
                          )}
                        </Grid>
                        <Grid item xs={12}>
                          <Restricted to={PERMISSIONS_TYPE.SWDS_CREATE_BUNDLE}>
                            <Grid container direction="row" justifyContent="flex-end">
                              <Button
                                disabled={!isAllowed(permission)}
                                variant="contained"
                                size="large"
                                onClick={() => setOpenModal(true)}
                              >
                                Create New Bundle
                              </Button>
                            </Grid>
                          </Restricted>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                  <Accordion defaultExpanded={true}>
                    <AccordionSummary aria-controls="comments-accordion" id="comments-accordion">
                      <Typography>Comments</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <CommentsList profileId={profileData.id} />
                    </AccordionDetails>
                  </Accordion>
                </>
              ) : null}
            </Grid>
            <Grid item xs={12}>
              <Grid container direction="row" spacing={3} justifyContent="center" alignItems="center">
                <Grid item>
                  <Button variant="contained" size="large" onClick={() => handleCloseWithRedirect()}>
                    Cancel
                  </Button>
                </Grid>
                <Grid item>
                  <LoadingButton
                    disabled={!isAllowed(permission)}
                    loading={loading}
                    variant="contained"
                    size="large"
                    onClick={handleSubmit(onSubmit)}
                  >
                    Save
                  </LoadingButton>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
          <BundleModal
            actionType={bundleActionType}
            open={openModal}
            onClose={() => {
              setOpenModal(false);
              setBundleActionType(ActionType.CREATE);
            }}
            profileBundleHandler={profileBundleMutate}
            cloneBundle={cloneBundle}
          />
          {selectedRow ? (
            <ConfirmDialog
              open={openDialog}
              setOpen={setOpenDialog}
              message={`Are you sure you would like to delete "${selectedRow.name}" bundle?`}
              onConfirm={dialogConfirmAction}
            />
          ) : null}
          <Snackbar
            open={submitSuccess.isSuccess || submitError.open}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
          >
            {submitSuccess.isSuccess ? (
              <Alert onClose={handleClose} severity="success" sx={{ width: '100%' }}>
                {actionType === ActionType.CREATE || actionType === ActionType.CLONE
                  ? 'Profile has been successfully created!'
                  : actionType === ActionType.IMPORT || actionType === ActionType.EDIT_BY_IMPORT
                  ? 'Profile has been successfully imported!'
                  : 'Profile has been edited successfully!'}
              </Alert>
            ) : submitError.open ? (
              <Alert onClose={handleClose} severity="error" sx={{ width: '100%' }}>
                {actionType === ActionType.IMPORT || actionType === ActionType.EDIT_BY_IMPORT
                  ? 'Error importing profile: ' + submitError.message
                  : actionType === ActionType.CREATE || actionType === ActionType.CLONE
                  ? submitError.message
                    ? 'Error creating profile: ' + submitError.message
                    : 'Error creating profile...'
                  : submitError.message
                  ? 'Error editing profile: ' + submitError.message
                  : 'Error editing profile...'}
              </Alert>
            ) : undefined}
          </Snackbar>
        </>
      )}
    </>
  );
}

// @ts-nocheck TODO: temp
import React, { useEffect } from 'react';
import Modal from '@mui/material/Modal';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { object, string } from 'yup';
import Button from '@mui/material/Button';
import DeleteIcon from '@mui/icons-material/DeleteForever';
import {
  Autocomplete,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
} from '@mui/material';
import { useMutation, useQuery } from 'react-query';
import Alert from '@mui/material/Alert';
import TextField from '@mui/material/TextField';
import { ActionType } from '../../types';
import { FormInput, FormTextArea } from '../controls';
import { Accordion, AccordionDetails, AccordionSummary } from '../Accordion';
import { LoadingButton } from '@mui/lab';
import useHttpClient from '../../hooks/useHttpClient';

const style = {
  position: 'absolute' as 'absolute',
  display: 'flex',
  alignItems: 'center',
  flexDirection: 'column',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  height: '40vw',
  width: '60vw',
  // height: '80vh',
  bgcolor: 'background.paper',
  // border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  overflow: 'auto',
};

export function BundleModal(props: any) {
  const { open, onClose, profileBundleHandler, actionType, cloneBundle } = props;
  const httpClient = useHttpClient();
  const [q, setSearchQuery] = React.useState('');
  const [packages, setPackages] = React.useState<[]>([]);
  const [categories, setCategories] = React.useState<string[]>([]);
  const [openSnackbar, setOpenSnackbar] = React.useState({ open: false, message: '' });

  const [packageSelected, setPackageSelected] = React.useState('');
  const [versionSelected, setVersionSelected] = React.useState('');
  const [categorySelected, setCategorySelected] = React.useState('');
  const [useLegacy, setUseLegacy] = React.useState(false);

  const [hashPackages, setHashPackages] = React.useState({});

  const [loading, setLoading] = React.useState(false);

  const schema = object().shape({
    name: string().required('Bundle Name is required'),
    description: string().required('Bundle Description is required'),
    use_legacy: string().optional('Bundle Use Legacy is optional'),
  });
  const {
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
  });

  const resetHandler = () => {
    reset();
    setPackageSelected('');
    setVersionSelected('');
    setCategorySelected('');
    setUseLegacy(false);
    setHashPackages({});
    onClose();
  };

  const createBundle = async (data: any) => {
    const response = await httpClient.post('/api/bundles', data);
    console.log('createBundle', response);
    return response;
  };

  const { mutate: createMutate } = useMutation(createBundle, {
    onSuccess: (data: any) => {
      console.log('useMutation createBundle onSuccess', data);
      resetHandler();
      profileBundleHandler([data.name]);
    },
    onError: (error: Error) => {
      console.log('useMutation createBundle onError', error);
      setOpenSnackbar({ open: true, message: error.message });
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  const onSubmit = (data: any) => {
    setLoading(true);
    let packages = [];
    Object.keys(hashPackages).forEach((key: string) => {
      packages = packages.concat(hashPackages[key]);
    });
    createMutate({ ...data, packages });
  };

  const {
    isLoading: listPackagesIsLoading,
    error: listPackagesError,
    data: listPackages,
  } = useQuery('listPackages', () => {
    return httpClient.get(`/api/packages?p=${1}&ps=${5000}&q=${q}`);
  });

  useEffect(() => {
    if (cloneBundle) {
      cloneBundle.name = undefined;
      reset({ ...cloneBundle });
      let cloneBundlePackages = cloneBundle.packages.map((p) => {
        const matchPackage = packages.find((pack) => pack.name === p.name);
        const matchPackageVersion = p.version;
        const matchPackageLegacy = p.use_legacy;

        return matchPackageVersion && matchPackageVersion.length > 0
          ? { ...matchPackage, version: matchPackageVersion, use_legacy: matchPackageLegacy }
          : null;
      });
      cloneBundlePackages = cloneBundlePackages.filter((item) => item !== null);
      for (const clonePackage of cloneBundlePackages) {
        let packages = hashPackages[clonePackage.category] || [];
        packages.push({ name: clonePackage.name, version: clonePackage.version, use_legacy: clonePackage.use_legacy });
        hashPackages[clonePackage.category] = packages;
        setHashPackages(hashPackages);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cloneBundle]);

  useEffect(() => {
    if (!listPackagesIsLoading && !listPackagesError && listPackages && Array.isArray(listPackages.items)) {
      let category = [];
      for (const pack of listPackages.items) {
        category.push(pack.category);
      }
      setPackages(listPackages.items);

      const uniqueCategories = new Set(category);
      setCategories(Array.from(uniqueCategories));

      if (packageSelected.length === 0 && listPackages.items.length > 0) {
        setPackageSelected(listPackages.items[0].name);
        setCategorySelected(listPackages.items[0].category);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listPackages, categories]);

  const getPackageVersions = () => {
    const pack = listPackages.items.find((pack: any) => pack.name === packageSelected);
    return pack ? pack.versions : [];
  };

  const onPackageSelect = (event: SelectChangeEvent) => {
    setPackageSelected(event.target.value);
    setVersionSelected('');
    const pack = listPackages.items.find((pack: any) => pack.name === event.target.value);
    setCategorySelected(pack.category);
  };

  const onVersionSelect = (event, newValue) => {
    if (!newValue && event.target.value) {
      setVersionSelected(event.target.value);
    } else {
      setVersionSelected(newValue);
    }
  };

  const onCategorySelect = (event: SelectChangeEvent) => {
    setCategorySelected(event.target.value);
  };

  const onUseLegacyCheck = (event) => {
    setUseLegacy(event.target.checked);
  };

  const addPackage = () => {
    if (hasError(categorySelected) || hasError(packageSelected) || hasError(versionSelected) || hasError(useLegacy)) {
      return;
    }
    let packages = hashPackages[categorySelected] || [];

    const duplicate = packages.filter(
      (p) => p.name === packageSelected && p.version === versionSelected
    );
    if (duplicate && duplicate.length > 0) {
      return;
    }
    if (!packages.some((p) => p.name === packageSelected)) {
      packages.push({ name: packageSelected, version: versionSelected, use_legacy: useLegacy });
    } else {
      setOpenSnackbar({ open: true, message: ' Bundles can only have one package version' });
    }
    hashPackages[categorySelected] = packages;
    setHashPackages(hashPackages);
  };

  const removePackage = (category, pack) => {
    let packages = hashPackages[category];
    packages = packages.filter((p) => (p.name === pack.name && p.version !== pack.version) || p.name !== pack.name);
    hashPackages[category] = packages;
    setHashPackages(hashPackages);
  };

  const hasError = (data) => {
    if (!data && data !== false || data.length <= 0) {
      return true;
    }
    return false;
  };

  const renderPackages = () => {
    return (
      <>
        {categories.map((menuItem: any, index: number) => {
          return (
            <Grid item xs={12} key={menuItem + index}>
              <Accordion defaultExpanded={true}>
                <AccordionSummary aria-controls={`${menuItem}`} id={`${menuItem}`}>
                  <Typography>{menuItem}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {hashPackages && hashPackages[menuItem] ? (
                    <TableContainer component={Paper}>
                      <Table sx={{ minWidth: 650 }} aria-label={`${menuItem}`}>
                        <TableBody>
                          {hashPackages[menuItem].map((row, index: number) => (
                            <TableRow key={row.name + index} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                              <TableCell align="left" sx={{ width: '50%' }}>
                                {row.name}
                              </TableCell>
                              <TableCell align="left" sx={{ width: '20%' }}>
                                {row.version}
                              </TableCell>
                              <TableCell align="right" sx={{ width: '5%' }}>
                                {row.use_legacy === true ? "Legacy" : ""}
                              </TableCell>
                              <TableCell align="right" sx={{ width: '25%' }}>
                                <DeleteIcon
                                  sx={{ cursor: 'pointer' }}
                                  onClick={() => removePackage(menuItem, row)}
                                ></DeleteIcon>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : null}
                </AccordionDetails>
              </Accordion>
            </Grid>
          );
        })}
      </>
    );
  };

  const handleSnackbarClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    setOpenSnackbar({ open: false, message: '' });
  };

  const handleModalOnClose = () => {
    resetHandler();
    onClose();
  };

  return (
    <>
      <Modal
        open={open}
        onClose={() => handleModalOnClose()}
        aria-labelledby="bundle-modal"
        aria-describedby="bundle-modal"
      >
        <Box sx={style}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
                {actionType === ActionType.CLONE ? 'Clone Bundle' : 'Add Bundle'}
              </Typography>
            </Grid>
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
                  label={'Enter Bundle Name'}
                  error={errors.name}
                />
              </Box>
            </Grid>
            <Grid item xs={12}>
              <FormTextArea
                control={control}
                name={'description'}
                ariaLabel={'Enter Bundle Description'}
                placeholder={'Enter Bundle Description'}
                minRows={4}
                style={{ width: '100%' }}
                error={errors.description}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h5" noWrap component="div">
                Add New Package:
              </Typography>
            </Grid>
            {listPackagesIsLoading || !listPackages || packages.length <= 0 ? (
              <div>Loading Packages ...</div>
            ) : listPackagesError ? (
              <div>An error has occurred for loading Packages</div>
            ) : (
              <>
                <Grid item xs={12}>
                  <Grid container spacing={3} alignItems="center">
                    <Grid item xs={5}>
                      <Box>
                        <FormControl fullWidth error={hasError(packageSelected)}>
                          <InputLabel id={'package-label'}>Package</InputLabel>
                          <Select
                            labelid={'package-label'}
                            id={'package'}
                            label={'Package'}
                            value={packageSelected}
                            onChange={onPackageSelect}
                          >
                            {packages.map((menuItem: any) => {
                              return (
                                <MenuItem key={menuItem.name} value={menuItem.name}>
                                  {menuItem.name}
                                </MenuItem>
                              );
                            })}
                          </Select>
                        </FormControl>
                      </Box>
                    </Grid>
                    <Grid item xs={2}>
                      <FormControl fullWidth error={hasError(versionSelected)}>
                        <Autocomplete
                          value={versionSelected}
                          id="list-versions"
                          freeSolo
                          getOptionLabel={(version: any) => version}
                          options={getPackageVersions()}
                          onChange={onVersionSelect}
                          onInput={onVersionSelect}
                          renderInput={(params) => <TextField {...params} label="Version" />}
                        />
                      </FormControl>
                    </Grid>
                    <Grid item xs={3}>
                      <Box>
                        <FormControl fullWidth error={hasError(categorySelected)}>
                          <InputLabel id={'category-label'}>Category</InputLabel>
                          <Select
                            labelid={'category-label'}
                            id={'category'}
                            label={'Category'}
                            value={categorySelected}
                            onChange={onCategorySelect}
                            disabled={true}
                          >
                            {categories.map((menuItem: any) => {
                              return (
                                <MenuItem key={menuItem} value={menuItem}>
                                  {menuItem}
                                </MenuItem>
                              );
                            })}
                          </Select>
                        </FormControl>
                      </Box>
                    </Grid>

                    <Grid item xs={2}>
                      <Box>
                        <FormControl fullWidth error={hasError(useLegacy)}>
                          <FormControlLabel
                            label="Use Legacy"
                            control={<Checkbox value={useLegacy} />}
                            labelid={'use-legacy-label'}
                            id={'use-legacy'}
                            value={useLegacy}
                            onChange={onUseLegacyCheck}
                          />
                        </FormControl>
                      </Box>
                    </Grid>

                    <Grid item>
                      <Button variant="contained" size="large" onClick={() => addPackage()}>
                        Add
                      </Button>
                    </Grid>
                  </Grid>
                </Grid>
                {renderPackages()}
              </>
            )}
            <Grid item xs={12}>
              <Grid container direction="row" spacing={3} justifyContent="center" alignItems="center">
                <Grid item>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => {
                      resetHandler();
                    }}
                  >
                    Cancel
                  </Button>
                </Grid>
                <Grid item>
                  <LoadingButton loading={loading} variant="contained" size="large" onClick={handleSubmit(onSubmit)}>
                    Save
                  </LoadingButton>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </Box>
      </Modal>
      <Snackbar
        open={openSnackbar.open}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        autoHideDuration={5000}
        onClose={handleSnackbarClose}
      >
        <Alert onClose={handleSnackbarClose} severity="error" sx={{ width: '100%' }}>
          {openSnackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}

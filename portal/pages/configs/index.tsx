import React from 'react';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Link from 'next/link';
import { ConfirmDialog, Table } from '../../components';
import { useRouter } from 'next/router';
import useHttpClient from '../../hooks/useHttpClient';
import { useQuery, useQueryClient } from 'react-query';
import Restricted from '../../components/controls/Restricted';
import { ActionType, PERMISSIONS_TYPE } from '../../types';
import { Snackbar } from '@mui/material';
import Alert from '@mui/material/Alert';
import { string } from 'yup';

interface Column {
  id: 'name' | 'path' | 'current' | 'inherits' | 'description' | 'created' | 'updated' | 'created_by' | 'actions';
  label: string;
  minWidth?: number;
  align?: 'right';
  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: 'name', label: 'Config', minWidth: 100 },
  { id: 'path', label: 'Level', minWidth: 100 },
  { id: 'current', label: 'Active', minWidth: 100 },
  { id: 'inherits', label: 'Inherits', minWidth: 100 },
  { id: 'description', label: 'Description', minWidth: 200 },
  { id: 'created', label: 'Create Date', minWidth: 100 },
  { id: 'updated', label: 'Updated', minWidth: 100 },
  { id: 'created_by', label: 'Author', minWidth: 100 },
  { id: 'actions', label: '', minWidth: 100 },
];

interface Configuration {
  id: string;
  name: string;
  path: string;
  level: any;
  description: string;
  inherits: boolean;
  created: string;
  updated: string;
  created_by: string;
}

interface RowData {
  id: string;
  name: string;
  path: string;
  // level: string;
  description: string;
  inherits: boolean;
  created: string;
  updated: string;
  created_by: string;
}

function createRows(data: any): RowData[] {
  const configurations: Configuration[] = data.items;
  let rows: RowData[] = [];
  for (const c of configurations) {
    let configuration: Configuration = c;
    rows.push({
      ...configuration,
    });
  }
  return rows;
}

async function fetchConfigs(httpClient: any, p: number = 1, ps: number = 10, q: string = '') {
  return httpClient.get(`/api/configs?p=${p}&ps=${ps}&name=${q}`);
}

async function deleteConfig(httpClient: any, id: string) {
  const response = await httpClient.delete(`/api/configs/${id}`);
  console.log('deleteConfig', response);
  return 'Configuration deleted successfully';
}

async function updateConfigStatus(httpClient: any, id: any, activate: boolean) {
  const response = await httpClient.put(`/api/configs/${id}/status`, { current: activate });
  console.log('updateConfigStatus', response);
  return response;
}

export default function ManageConfigs() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const queryClient = useQueryClient();
  const [p, setPage] = React.useState(1);
  const [ps, setPageSize] = React.useState(10);
  const [q, setSearchQuery] = React.useState('');
  const [searchTimer, setTimer] = React.useState(null);
  const searchInput = React.useRef<any>('');
  const [openDialog, setOpenDialog] = React.useState(false);
  const [selectedRow, setSelectedRow] = React.useState<RowData>();
  const [openSnackbar, setOpenSnackbar] = React.useState({ open: false, message: '' });

  const {
    status,
    data: configsData,
    error: configsError,
    isFetching,
  } = useQuery(['configsData', p, ps, q], () => fetchConfigs(httpClient, p, ps, q));

  // Prefetch the next page!
  React.useEffect(() => {
    if (configsData?.navigation?.next) {
      queryClient.prefetchQuery(['configsData', p + 1, ps, q], () => fetchConfigs(httpClient, p + 1, ps, q));
    }
  }, [configsData, p, ps, q, queryClient, httpClient]);

  const handleChangePage = (newPage: number) => {
    setPage(newPage);
  };

  const handleChangePageSize = (pageSize: number) => {
    setPageSize(pageSize);
  };

  const dialogConfirmAction = async () => {
    if (selectedRow) {
      try {
        const response = await deleteConfig(httpClient, selectedRow.id);
        setSelectedRow(undefined);
        setOpenSnackbar({ open: true, message: response });
        await queryClient.invalidateQueries(['configsData']);
        await queryClient.refetchQueries(['configsData'], { active: true });
      } catch (error) {
        setOpenSnackbar({ open: true, message: error?.message });
      }
    }
  };

  const handleTableRowActions = async (action: string, row: any) => {
    if (action === ActionType.ACTIVE || action === ActionType.DEACTIVATE) {
      try {
        updateConfigStatus(httpClient, row.id, action === ActionType.ACTIVE);
        await queryClient.invalidateQueries(['configsData']);
        await queryClient.refetchQueries(['configsData'], { active: true });
        setOpenSnackbar({
          open: true,
          message: `${row.name} configuration ${action === ActionType.ACTIVE ? 'activated' : 'deactivated'}`,
        });
      } catch (error) {
        setOpenSnackbar({
          open: true,
          message: Array.isArray(error?.response?.data?.message)
            ? JSON.stringify(error?.response?.data?.message)
            : error?.response?.data?.message || error?.message,
        });
      }
    }
    if (action === ActionType.EDIT || action === ActionType.VIEW) {
      router.push(`/configs/edit/${row.id}`);
    }
    if (action === ActionType.DELETE) {
      setSelectedRow(row);
      setOpenDialog(true);
    }
  };

  const handleSnackbarClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    setOpenSnackbar({ open: false, message: '' });
  };

  const handleSearch = (searchQuery: string) => {
    let timerId: any = window.setTimeout(() => {
      setSearchQuery('~'+searchQuery);
      setPage(1);
    }, 1000);

    if (searchTimer) {
      clearTimeout(searchTimer);
      setTimer(null);
    }

    setTimer(timerId);
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
          Manage Configurations
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={11}>
            <Restricted to={PERMISSIONS_TYPE.CONFIG_VIEW_CONFIG}>
              <Box
                sx={{
                  maxWidth: '100%',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'row' }}>
                  <TextField
                    fullWidth
                    label="Search configurations by name"
                    id="fullWidth"
                    inputRef={searchInput}
                    onKeyUp={(e) => {
                      handleSearch((e.target as HTMLButtonElement).value);
                    }}
                  />
                </div>
              </Box>
            </Restricted>
          </Grid>
          <Grid item>
            <Restricted to={PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG}>
              <Link href={'/configs/create'} passHref>
                <Button style={{ backgroundColor: 'black', width: '100%' }} variant="contained" size="large">
                  Create
                </Button>
              </Link>
            </Restricted>
          </Grid>
        </Grid>
        <Restricted to={PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG}>
          <Grid container>
            <Grid item>
              <div style={{ display: 'flex', flexDirection: 'row' }}>
                <Typography variant="caption" gutterBottom style={{ marginTop: '1em' }}>
                  Start your search term with ~ for partial matching
                </Typography>
              </div>
            </Grid>
          </Grid>
        </Restricted>
      </Grid>
      <Grid item xs={12}>
        {isFetching || status === 'loading' ? (
          <div>Loading...</div>
        ) : configsError ? (
          <div>An error has occurred</div>
        ) : (
          <Restricted to={PERMISSIONS_TYPE.CONFIG_VIEW_CONFIG}>
            <Table
              columns={columns}
              rows={createRows(configsData)}
              actions={['Edit', 'View', 'Active', 'Deactivate', 'Delete']}
              permissions={[
                PERMISSIONS_TYPE.CONFIGS_UPDATE_CONFIG,
                PERMISSIONS_TYPE.CONFIG_VIEW_CONFIG,
                PERMISSIONS_TYPE.CONFIGS_CREATE_CONFIG,
                PERMISSIONS_TYPE.CONFIGS_UPDATE_CONFIG,
                PERMISSIONS_TYPE.CONFIG_DELETE_CONFIG,
              ]}
              total={configsData?.navigation?.total}
              page={p}
              pageSize={ps}
              pageChangeHandler={handleChangePage}
              pageSizeChangeHandler={handleChangePageSize}
              tableRowActionHandler={handleTableRowActions}
            />
          </Restricted>
        )}
      </Grid>
      {selectedRow ? (
        <ConfirmDialog
          open={openDialog}
          setOpen={setOpenDialog}
          message={`Are you sure you would like to delete "${selectedRow.name}" configuration?`}
          onConfirm={dialogConfirmAction}
        />
      ) : null}
      <Snackbar
        open={openSnackbar.open}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        autoHideDuration={5000}
        onClose={handleSnackbarClose}
      >
        <Alert onClose={handleSnackbarClose} severity="info" sx={{ width: '100%' }}>
          {openSnackbar.message}
        </Alert>
      </Snackbar>
    </Grid>
  );
}

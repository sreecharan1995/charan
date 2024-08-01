import React from 'react';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Link from 'next/link';
import { useQuery, useQueryClient } from 'react-query';
import { useRouter } from 'next/router';
import { ConfirmDialog, Table } from '../../components';
import { Snackbar } from '@mui/material';
import Alert from '@mui/material/Alert';
import Restricted from '../../components/controls/Restricted';
import { ActionType, PERMISSIONS_TYPE } from '../../types';
import useHttpClient from '../../hooks/useHttpClient';

interface Column {
  id: 'name' | 'description' | 'path' | 'profile_status' | 'created_by' | 'created_at' | 'actions';
  label: string;
  minWidth?: number;
  align?: 'right';
  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: 'name', label: 'Name', minWidth: 100 },
  { id: 'description', label: 'Description', minWidth: 200 },
  { id: 'path', label: 'Target Level', minWidth: 200 },
  {
    id: 'profile_status',
    label: 'Status',
    minWidth: 100,
  },
  {
    id: 'created_by',
    label: 'Created by',
    minWidth: 100,
  },
  {
    id: 'created_at',
    label: 'Created',
    minWidth: 100,
  },
  {
    id: 'actions',
    label: '',
    minWidth: 100,
  },
];

interface Profile {
  id: string;
  name: string;
  description: string;
  path: string;
  profile_status: string;
  created_by: string;
  created_at: string;
}

interface RowData {
  id: string;
  name: string;
  description: string;
  path: string;
  profile_status: string;
  created_by: string;
}

function createRows(data: any): RowData[] {
  const profiles: Profile[] = data.items;
  let rows: RowData[] = [];
  for (const p of profiles) {
    const profile: Profile = p;
    rows.push({
      ...profile,
    });
  }
  return rows;
}

async function fetchProfiles(httpClient: any, p: number = 1, ps: number = 10, q: string = '') {
  return httpClient.get(`/api/profiles?p=${p}&ps=${ps}&q=${q}`);
}

async function deleteProfile(httpClient: any, id: string) {
  const response = await httpClient.delete(`/api/profiles/${id}`);
  console.log('deleteProfile', response);
  return 'Profile deleted successfully';
}

export default function ManageProfiles() {
  const router = useRouter();
  const httpClient = useHttpClient();
  const queryClient = useQueryClient();
  const [p, setPage] = React.useState(1);
  const [ps, setPageSize] = React.useState(10);
  const [q, setSearchQuery] = React.useState('');
  const [searchTimer, setTimer] = React.useState(null);
  const [openDialog, setOpenDialog] = React.useState(false);
  const [selectedRow, setSelectedRow] = React.useState<RowData>();
  const searchInput = React.useRef<any>('');
  const [openSnackbar, setOpenSnackbar] = React.useState({ open: false, message: '' });

  const {
    status,
    data: profilesData,
    error: profilesError,
    isFetching,
  } = useQuery(['profilesData', p, ps, q], () => fetchProfiles(httpClient, p, ps, q), { keepPreviousData: true });

  // Prefetch the next page!
  React.useEffect(() => {
    if (profilesData?.navigation?.next) {
      queryClient.prefetchQuery(['profilesData', p + 1, ps, q], () => fetchProfiles(httpClient, p + 1, ps, q));
    }
  }, [profilesData, p, ps, q, queryClient, httpClient]);

  const handleChangePage = (newPage: number) => {
    setPage(newPage);
  };

  const handleChangePageSize = (pageSize: number) => {
    setPageSize(pageSize);
  };

  const dialogConfirmAction = async () => {
    if (selectedRow) {
      try {
        const response = await deleteProfile(httpClient, selectedRow.id);
        setSelectedRow(undefined);
        setOpenSnackbar({ open: true, message: response });
        await queryClient.refetchQueries(['profilesData']);
      } catch (error) {
        setOpenSnackbar({ open: true, message: error?.message });
      }
    }
  };

  const handleTableRowActions = (action: string, row: any) => {
    if (action === ActionType.EDIT || action === ActionType.VIEW || action === ActionType.EDIT_BY_IMPORT) {
      const editByImport = action === ActionType.EDIT_BY_IMPORT ? 1 : 0;
      router.push({ pathname: `/swds/edit/${row.id}`, query: { editByImport } });
    }
    if (action === ActionType.CLONE) {
      router.push({ pathname: `/swds/edit/${row.id}`, query: { clone: 1 } });
    }
    if (action === ActionType.DELETE) {
      setSelectedRow(row);
      setOpenDialog(true);
    }
  };

  const handleProfileSearch = (searchQuery: string) => {
    let timerId: any = window.setTimeout(() => {
      setSearchQuery(searchQuery);
      setPage(1);
    }, 1000);

    if (searchTimer) {
      clearTimeout(searchTimer);
      setTimer(null);
    }

    setTimer(timerId);
  };

  const clearSearch = () => {
    searchInput.current.value = '';
    setSearchQuery('');
    setPage(1);
  };

  const handleSnackbarClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    setOpenSnackbar({ open: false, message: '' });
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
          Manage Profiles
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={11}>
            <Restricted to={PERMISSIONS_TYPE.SWDS_VIEW_PROFILE}>
              <Box
                sx={{
                  maxWidth: '100%',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'row' }}>
                  <TextField
                    fullWidth
                    label="Search profiles by name, description or status"
                    id="fullWidth"
                    inputRef={searchInput}
                    onKeyUp={(e) => {
                      handleProfileSearch((e.target as HTMLButtonElement).value);
                    }}
                  />
                  <Button onClick={() => clearSearch()} className="materialBtn">
                    Clear
                  </Button>
                </div>
              </Box>
            </Restricted>
          </Grid>
          <Grid item>
            <Restricted to={PERMISSIONS_TYPE.SWDS_CREATE_PROFILE}>
              <Link href={'/swds/create'} passHref>
                <Button style={{ backgroundColor: 'black' }} variant="contained" size="large">
                  Create
                </Button>
              </Link>
              <Link href={'/swds/import'} passHref>
                <Button style={{ backgroundColor: '#3C99DC', marginLeft: '10px' }} variant="contained" size="large">
                  Import
                </Button>
              </Link>
            </Restricted>
          </Grid>
        </Grid>
      </Grid>
      <Grid item xs={12}>
        {isFetching || status === 'loading' ? (
          <div>Loading...</div>
        ) : profilesError ? (
          <div>An error has occurred</div>
        ) : (
          <Restricted to={PERMISSIONS_TYPE.SWDS_VIEW_PROFILE}>
            <Table
              columns={columns}
              rows={createRows(profilesData)}
              actions={['Edit', 'Update from XML', 'View', 'Clone', 'Delete']}
              permissions={[
                PERMISSIONS_TYPE.SWDS_UPDATE_PROFILE,
                PERMISSIONS_TYPE.SWDS_UPDATE_PROFILE,
                PERMISSIONS_TYPE.SWDS_VIEW_PROFILE,
                PERMISSIONS_TYPE.SWDS_CREATE_PROFILE,
                PERMISSIONS_TYPE.SWDS_DELETE_PROFILE,
              ]}
              total={profilesData?.navigation?.total}
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
          message={`Are you sure you would like to delete "${selectedRow.name}" profile?`}
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

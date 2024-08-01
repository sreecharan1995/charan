import * as React from 'react';
import Paper from '@mui/material/Paper';
import { Button, Table as MaterialTable } from '@mui/material';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import { TableRowPopoverActions } from './';

export function Table(props: any) {
  const {
    columns,
    rows,
    total,
    page,
    pageSize,
    pageChangeHandler,
    pageSizeChangeHandler,
    actions,
    permissions,
    tableRowActionHandler,
    disabled,
    disabledPagination,
  } = props;
  const [pg, setPg] = React.useState(page > 1 ? page - 1 : 0);
  const [rowsPerPage, setRowsPerPage] = React.useState(pageSize > 0 ? pageSize : 10);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPg(newPage);
    if (pageChangeHandler) {
      pageChangeHandler(newPage + 1);
    }
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(event.target.value);
    setPg(0);
    if (pageSizeChangeHandler) {
      pageSizeChangeHandler(event.target.value);
    }
    if (pageChangeHandler) {
      pageChangeHandler(1);
    }
  };

  const getItemColor = (value: string) => {
    if (value === 'deleted') {
      return 'red';
    } else if (value === 'pending') {
      return 'orange';
    } else if (value === 'valid') {
      return 'green';
    } else if (value === 'invalid') {
      return 'dimgray';
    }
    return 'inherit';
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 440 }}>
        <MaterialTable stickyHeader aria-label="sticky table">
          <TableHead>
            <TableRow>
              {columns &&
                Array.isArray(columns) &&
                columns.map((column: any) => (
                  <TableCell
                    key={column.id}
                    align={column.align}
                    style={{ minWidth: column.minWidth, backgroundColor: 'black', color: 'white' }}
                  >
                    {column.label}
                  </TableCell>
                ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows &&
              Array.isArray(rows) &&
              rows.map((row: any) => {
                return (
                  <TableRow hover role="checkbox" tabIndex={-1} key={row.id + row.name}>
                    {columns.map((column: any) => {
                      const value = row[column.id];
                      if (column.id === 'actions') {
                        if (disabled) {
                          return <TableCell key={column.id} align={column.align}></TableCell>;
                        }
                        return (
                          <TableCell key={column.id} align={column.align}>
                            <TableRowPopoverActions
                              actions={actions}
                              permissions={permissions}
                              label={'...'}
                              row={row}
                              tableRowActionHandler={tableRowActionHandler}
                            />
                          </TableCell>
                        );
                      }
                      if (column.id === 'name') {
                        return (
                          <TableCell key={column.id} align={column.align} sx={{ fontWeight: 'bold' }}>
                            {column.format && typeof value === 'number' ? column.format(value) : value}
                          </TableCell>
                        );
                      }
                      if (column.id === 'profile_status') {
                        return (
                          <TableCell key={column.id} align={column.align} sx={{ fontWeight: 'bold' }}>
                            <Button
                              size={'small'}
                              variant={'contained'}
                              disableElevation={true}
                              sx={{ color: 'white', backgroundColor: getItemColor(value) }}
                            >
                              {column.format && typeof value === 'number' ? column.format(value) : value}
                            </Button>
                          </TableCell>
                        );
                      }
                      if (column.id === 'created_at') {
                        return (
                          <TableCell key={column.id} align={column.align}>
                            {value.replace('T', ' ')}
                          </TableCell>
                        );
                      }
                      return (
                        <TableCell key={column.id} align={column.align}>
                          {column.format && typeof value === 'number' ? column.format(value) : String(value)}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
          </TableBody>
        </MaterialTable>
      </TableContainer>
      {disabledPagination ? null : (
        <TablePagination
          rowsPerPageOptions={[10, 25, 100]}
          component="div"
          count={total ? total : rows ? rows.length : 0}
          rowsPerPage={rowsPerPage}
          page={pg}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      )}
    </Paper>
  );
}

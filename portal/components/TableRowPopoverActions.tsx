import * as React from 'react';
import { useEffect } from 'react';
import Popover from '@mui/material/Popover';
import Button from '@mui/material/Button';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import usePermission from '../hooks/usePermission';
import { ActionType } from '../types';
import { ContentCopy, DeleteForever, Edit, ToggleOff, ToggleOn, UploadFile, Visibility } from '@mui/icons-material';

export function TableRowPopoverActions(props: any) {
  const { label, row, actions, permissions, tableRowActionHandler } = props;
  const [anchorEl, setAnchorEl] = React.useState<HTMLButtonElement | null>(null);
  const [options, setOptions] = React.useState<string[]>(actions || ['Edit', 'Clone', 'Delete']);
  const isAllowed = usePermission();

  const handlePopoverClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };

  const handleRowAction = (text: any, row: any) => {
    if (tableRowActionHandler) {
      tableRowActionHandler(text, row);
    }
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);
  const id = open ? 'table-row-popover-actions' : undefined;

  useEffect(() => {
    if (options && options.length > 0 && permissions && permissions.length === options.length) {
      let filters: Array<number> = [];
      options.forEach((option: string, index: number) => {
        if (!isAllowed(permissions[index])) {
          filters.push(index);
        }
      });
      let optionsFiltered = options
        .filter((value, index) => {
          return filters.indexOf(index) === -1;
        })
        .filter((value, index) => {
          if (value === ActionType.ACTIVE) {
            return !row.current;
          }
          if (value === ActionType.DEACTIVATE) {
            return row.current;
          }

          const profilePattern = /^profile_/i;
          const isProfile = profilePattern.test(row.id);

          if ((value === ActionType.EDIT && row.current) || (value === ActionType.VIEW && !row.current && !isProfile)) {
            return false;
          }
          return true;
        });

      const viewIndex = optionsFiltered.findIndex((opt) => opt === ActionType.VIEW);
      const editIndex = optionsFiltered.findIndex((opt) => opt === ActionType.EDIT);
      // cannot have both edit/view dropdowns
      if (viewIndex >= 0 && editIndex >= 0) {
        optionsFiltered.splice(viewIndex, 1);
      }
      setOptions(optionsFiltered);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [permissions]);

  if (options.length === 0) {
    return null;
  }

  return (
    <>
      <Button aria-describedby={id} variant="text" onClick={handlePopoverClick}>
        <Typography sx={{ fontWeight: 'bold', fontSize: 20 }}>{label}</Typography>
      </Button>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handlePopoverClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        {options.map((text, index) => (
          <ListItem key={text} disablePadding sx={{ display: 'block' }} onClick={() => handleRowAction(text, row)}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                {text === 'Edit' ? (
                  <Edit />
                ) : text.includes('from XML') ? (
                  <UploadFile />
                ) : text === 'Clone' ? (
                  <ContentCopy />
                ) : text === 'Delete' ? (
                  <DeleteForever />
                ) : text === 'Active' ? (
                  <ToggleOn></ToggleOn>
                ) : text === 'Deactivate' ? (
                  <ToggleOff></ToggleOff>
                ) : text === 'View' ? (
                  <Visibility></Visibility>
                ) : null}
              </ListItemIcon>
              <ListItemText primary={text} sx={{ opacity: open ? 1 : 0 }} />
            </ListItemButton>
          </ListItem>
        ))}
      </Popover>
    </>
  );
}

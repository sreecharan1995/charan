import React from 'react';
import { Controller } from 'react-hook-form';
import { FormControl, FormHelperText, InputLabel, MenuItem, Select } from '@mui/material';

export function FormSelect(props: any) {
  const { control, selectId, name, labelId, label, error, menuItems } = props;
  return (
    <Controller
      control={control}
      render={({ field }) => (
        <FormControl fullWidth error={Boolean(!!error)}>
          <InputLabel id={labelId}>{label}</InputLabel>
          <Select labelId={labelId} id={selectId} label={label} {...field}>
            {menuItems.map((menuItem: any) => {
              return (
                <MenuItem key={menuItem.value} value={menuItem.value}>
                  {menuItem.label}
                </MenuItem>
              );
            })}
          </Select>
          <FormHelperText>{error ? error.message : ''}</FormHelperText>
        </FormControl>
      )}
      name={name}
      defaultValue={''}
    />
  );
}

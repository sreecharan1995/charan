import React from 'react';
import { Controller } from 'react-hook-form';
import { FormControl, FormControlLabel, Switch } from '@mui/material';

export function FormSwitch(props: any) {
  const { control, selectId, name, labelId, label, error, menuItems, disabled } = props;
  return (
    <Controller
      control={control}
      render={({ field }) => (
        <FormControl error={Boolean(!!error)}>
          <FormControlLabel
            control={<Switch checked={Boolean(field.value)} {...field} disabled={disabled} />}
            label={label}
          />
        </FormControl>
      )}
      name={name}
      defaultValue={false}
    />
  );
}

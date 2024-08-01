import React from 'react';
import { Controller } from 'react-hook-form';
import TextField from '@mui/material/TextField';

export function FormInput(props: any) {
  const { control, id, name, label, error, disabled } = props;
  return (
    <Controller
      control={control}
      render={({ field }) => (
        <TextField
          fullWidth
          label={label}
          error={Boolean(!!error)}
          helperText={error ? error.message : ''}
          id={id}
          disabled={disabled}
          {...field}
        />
      )}
      name={name}
      defaultValue={''}
    />
  );
}

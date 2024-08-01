import React from 'react';
import { Controller } from 'react-hook-form';
import { FormControl, TextareaAutosize, TextField } from '@mui/material';

export function FormTextArea(props: any) {
  const { control, name, ariaLabel, placeholder, minRows, style, error, disabled } = props;
  return (
    <Controller
      control={control}
      render={({ field }) => (
        <FormControl fullWidth error={Boolean(!!error)}>
          <TextField
            error={!!error}
            helperText={error ? error.message : ''}
            InputProps={{
              inputComponent: TextareaAutosize,
              inputProps: {
                'aria-label': ariaLabel,
                placeholder,
                minRows,
                style,
                ...field,
              },
            }}
            disabled={disabled}
          />
        </FormControl>
      )}
      name={name}
      defaultValue={''}
    />
  );
}

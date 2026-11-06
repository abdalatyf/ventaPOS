import React, { forwardRef } from 'react';
import AppAutocomplete from './common/AppAutocomplete';

const Autocomplete = forwardRef((props, ref) => {
  return <AppAutocomplete ref={ref} {...props} />;
});

export default Autocomplete;

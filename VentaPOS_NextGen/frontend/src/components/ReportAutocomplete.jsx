import React, { forwardRef } from 'react';
import AppAutocomplete from './common/AppAutocomplete';

/**
 * ReportAutocomplete — Unified Searchable Autocomplete Dropdown for Reports
 * Thin wrapper over AppAutocomplete with report styling defaults.
 */
const ReportAutocomplete = forwardRef(function ReportAutocomplete(props, ref) {
  return (
    <AppAutocomplete
      ref={ref}
      className="form-control form-control-sm"
      selectOnFocus={true}
      {...props}
    />
  );
});

export default ReportAutocomplete;

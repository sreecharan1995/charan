import Grid from '@mui/material/Grid';
import React, { useState } from 'react';
import Typography from '@mui/material/Typography';
import { Accordion, AccordionDetails, AccordionSummary } from '../';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import dynamic from 'next/dynamic';
import Button from '@mui/material/Button';
import { useRouter } from 'next/router';

const SvelteJSONEditor = dynamic(
  () => import('../SvelteJSONEditor'),
  { ssr: false } // <-- not including this component on server-side
);

interface Column {
  id:
    | 'profileName'
    | 'previousPackages'
    | 'includedPackages'
    | 'missedPackages'
    | 'ignoredPackages'
    | 'importedBundles'
    | 'importFailedBundles'
    | 'previousBundles'
    | 'includedBundles'
    | 'missedBundles'
    | 'ignoredBundles'
    | 'errors';
  label: string;
  minWidth?: number;
  align?: 'right';
  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: 'profileName', label: 'Profile Name', minWidth: 100 },
  { id: 'previousPackages', label: 'Previous Packages', minWidth: 100 },
  { id: 'includedPackages', label: 'Included Packages', minWidth: 100 },
  { id: 'missedPackages', label: 'Missed Packages', minWidth: 100 },
  { id: 'ignoredPackages', label: 'Ignored Packages', minWidth: 100 },
  { id: 'importedBundles', label: 'Imported Bundles', minWidth: 100 },
  { id: 'importFailedBundles', label: 'Imported Failed Bundles', minWidth: 100 },
  { id: 'previousBundles', label: 'Previous Bundles', minWidth: 100 },
  { id: 'includedBundles', label: 'Included Bundles', minWidth: 100 },
  { id: 'missedBundles', label: 'Missed Bundles', minWidth: 100 },
  { id: 'ignoredBundles', label: 'Ignored Bundles', minWidth: 100 },
  { id: 'errors', label: 'Errors', minWidth: 100 },
];

interface SummaryData {
  profileName: string;
  previousPackages: number;
  includedPackages: number;
  missedPackages: number;
  ignoredPackages: number;
  importedBundles: number;
  importFailedBundles: number;
  previousBundles: number;
  includedBundles: number;
  missedBundles: number;
  ignoredBundles: number;
  errors: number;
}

function createRows(summary: any): SummaryData[] {
  const summaryData: SummaryData = summary;
  if (!summary) return [];
  let rows: SummaryData[] = [summaryData];
  return rows;
}

type ContentType = {
  text?: string;
  json?: object;
};

export default function ImportResults(props: any) {
  const { bundles, errors, packages, summary } = props.data;
  const router = useRouter();
  const [packagesContent, setPackagesContent] = useState<ContentType>({ text: '', json: packages });
  const [bundlesContent, setBundlesContent] = useState<ContentType>({ text: '', json: bundles });
  const [errorsContent, setErrorsContent] = useState<ContentType>({ text: '', json: errors });

  return (
    <>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
            Import Profile Results
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Typography variant="h6" noWrap component="div" style={{ textAlign: 'left' }}>
            Summary
          </Typography>
          <TableContainer component={Paper}>
            <Table aria-label="Import Profile Results">
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
                {createRows(summary).map((row: any) => {
                  return (
                    <TableRow hover tabIndex={-1} key={row.id + row.name}>
                      {columns.map((column: any) => {
                        const value = row[column.id];
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
            </Table>
          </TableContainer>
        </Grid>
        <Grid item xs={12}>
          <Accordion defaultExpanded={false}>
            <AccordionSummary aria-controls="packages-accordion" id="packages-accordion">
              <Typography>Packages</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <div className="svelte-jsoneditor-react">
                <SvelteJSONEditor content={{ json: packagesContent }} readOnly={true} />
              </div>
            </AccordionDetails>
          </Accordion>
          <Accordion defaultExpanded={false}>
            <AccordionSummary aria-controls="bundles-accordion" id="bundles-accordion">
              <Typography>Bundles</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <div className="svelte-jsoneditor-react">
                <SvelteJSONEditor content={{ json: bundlesContent }} readOnly={true} />
              </div>
            </AccordionDetails>
          </Accordion>
          <Accordion defaultExpanded={false}>
            <AccordionSummary aria-controls="errors-accordion" id="errors-accordion">
              <Typography>Errors</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <div className="svelte-jsoneditor-react">
                <SvelteJSONEditor content={{ json: errorsContent }} readOnly={true} />
              </div>
            </AccordionDetails>
          </Accordion>
        </Grid>
        <Grid item xs={12}>
          <Grid container direction="row" spacing={3} justifyContent="center" alignItems="center">
            <Grid item>
              <Button
                variant="contained"
                size="large"
                onClick={() => {
                  router.push('/swds');
                }}
              >
                Done
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </>
  );
}

import type { NextPage } from 'next';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

const Home: NextPage = () => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" noWrap component="div" style={{ textAlign: 'center' }}>
          Welcome to the Spin Portal Homepage.
        </Typography>
      </Grid>
    </Grid>
  );
};

export default Home;

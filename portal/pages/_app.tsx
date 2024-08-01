import React, { useMemo } from 'react';
import '../styles/globals.css';
import '../styles/SvelteJSONEditor.css';
import type { AppProps } from 'next/app';
import { Hydrate, QueryClient, QueryClientProvider, useQuery } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { MsalProvider, useMsalAuthentication } from '@azure/msal-react';
import { EventMessage, EventType, InteractionType, PublicClientApplication } from '@azure/msal-browser';
import { msalConfig } from '../auth';
import Layout from '../components/layout/Layout';
import { AppProvider } from '../contexts';
import axios from 'axios';
import { QueryClientConfig } from 'react-query/types/core/types';

const getAuthInfo = async () => {
  const response = await axios.get('/api/auth');
  // console.log('authInfo', response);
  return response.data;
};

let msalInstance: any;

function MsalAuthProvider({ children }: { children: any }) {
  const { status, data, error, isFetching } = useQuery(['authInfo'], () => getAuthInfo(), {
    keepPreviousData: true,
    staleTime: 3600000,
  });

  if (isFetching || status === 'loading') {
    return null;
  }

  if (!msalInstance) {
    msalInstance = new PublicClientApplication(msalConfig(data['client_id'] as string, data['tenant_id'] as string));
    if (window && window.sessionStorage) {
      window.sessionStorage.setItem('msal_client_id', data['client_id']);
    }

    // Account selection logic is app dependent. Adjust as needed for different use cases.
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
    }

    msalInstance.addEventCallback((event: any) => {
      if (event.eventType === EventType.LOGIN_SUCCESS && event?.payload?.account) {
        const account = event.payload.account;
        msalInstance.setActiveAccount(account);
      }
    });
  }

  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>;
}

const queryClientConfig: QueryClientConfig = {
  defaultOptions: {
    queries: {
      keepPreviousData: false,
      refetchOnWindowFocus: false,
    },
  },
};

function MyApp({ Component, pageProps }: AppProps) {
  const queryClient = React.useRef(new QueryClient(queryClientConfig));

  return (
    <QueryClientProvider client={queryClient.current}>
      <Hydrate state={pageProps.dehydratedState}>
        <MsalAuthProvider>
          <AppProvider>
            <Layout>
              <Component {...pageProps} />
            </Layout>
          </AppProvider>
        </MsalAuthProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </Hydrate>
    </QueryClientProvider>
  );
}

export default MyApp;

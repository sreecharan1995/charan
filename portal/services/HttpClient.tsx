import { AuthenticationResult } from '@azure/msal-browser';

async function errorHandler(response: Response) {
  if (!response.ok) {
    const data = await response.json();
    if (data && Array.isArray(data.message)) {
      let msg;
      for (const message of data.message) {
        if (msg) {
          msg = msg + ', ' + message.msg;
        } else {
          msg = message.msg;
        }
      }
      throw Error(msg);
    }
    throw Error(data.message);
  }
  return response;
}

function acquireTokenAndFetch(
  account: any,
  instance: any,
  method: string,
  requestInfo: RequestInfo,
  data?: any,
  headers?: any,
  multipart?: boolean
) {
  let scopes = ['email profile openid'];
  if (window && window.sessionStorage) {
    const msalClientId = sessionStorage.getItem('msal_client_id');
    scopes = [`email profile openid ${msalClientId}/.default`];
  }

  return instance
    .acquireTokenSilent({
      scopes: scopes,
      account: account,
    })
    .then(async (authenticationResult: AuthenticationResult) => {
      return fetch(requestInfo, {
        headers: multipart
          ? { Authorization: `Bearer ${authenticationResult.accessToken}` }
          : {
              Authorization: `Bearer ${authenticationResult.accessToken}`,
              Accept: 'application/json',
              'Content-Type': 'application/json',
              ...headers,
            },
        method: method,
        body: multipart ? data : JSON.stringify(data),
      })
        .then(errorHandler)
        .then((res: Response) => {
          if (method === 'DELETE') {
            return res;
          }
          return res && res.json();
        });
    });
}

export function HttpClient(account: any, instance: any) {
  return {
    get: (requestInfo: RequestInfo) => {
      return acquireTokenAndFetch(account, instance, 'GET', requestInfo);
    },
    post: (requestInfo: RequestInfo, data?: any, headers?: any, multipart?: boolean) => {
      return acquireTokenAndFetch(account, instance, 'POST', requestInfo, data, headers, multipart);
    },
    patch: (requestInfo: RequestInfo, data: any) => {
      return acquireTokenAndFetch(account, instance, 'PATCH', requestInfo, data);
    },
    put: (requestInfo: RequestInfo, data: any, headers?: any, multipart?: boolean) => {
      return acquireTokenAndFetch(account, instance, 'PUT', requestInfo, data, headers, multipart);
    },
    delete: (requestInfo: RequestInfo) => {
      return acquireTokenAndFetch(account, instance, 'DELETE', requestInfo);
    },
  };
}

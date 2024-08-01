// Config object to be passed to Msal on creation
export function msalConfig(clientId: string, tenantId: string) {
  const authorityUrl = `https://login.microsoftonline.com/${tenantId}`;

  return {
    auth: {
      clientId: clientId,
      authority: authorityUrl,
      redirectUri: '/',
      postLogoutRedirectUri: '/',
      navigateToLoginRequestUrl: true,
    },
  };
}

// Add here scopes for id token to be used at MS Identity Platform endpoints.
export const loginRequest = {
  scopes: ['User.Read'],
};

// Add here the endpoints for MS Graph API services you would like to use.
export const graphConfig = {
  graphMeEndpoint: 'https://graph.microsoft-ppe.com/v1.0/me',
};

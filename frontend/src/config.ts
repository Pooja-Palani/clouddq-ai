/** Runtime config — replace after `sam deploy` or set via Amplify env. */
export const config = {
  region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
  userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
  userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3000',
  /** Local demo without Cognito — set VITE_DEV_AUTH=1 */
  devAuth: import.meta.env.VITE_DEV_AUTH === '1',
}

export type Role = 'DataUser' | 'BusinessUser'

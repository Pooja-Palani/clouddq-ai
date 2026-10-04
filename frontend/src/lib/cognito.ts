import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  CognitoUserSession,
} from 'amazon-cognito-identity-js'
import { config, type Role } from '../config'

export interface AuthUser {
  email: string
  sub: string
  role: Role
  token: string
}

function pool(): CognitoUserPool | null {
  if (!config.userPoolId || !config.userPoolClientId) return null
  return new CognitoUserPool({
    UserPoolId: config.userPoolId,
    ClientId: config.userPoolClientId,
  })
}

function groupsFromSession(session: CognitoUserSession): string[] {
  const payload = session.getIdToken().decodePayload()
  const groups = payload['cognito:groups']
  if (Array.isArray(groups)) return groups as string[]
  if (typeof groups === 'string') return [groups]
  return []
}

function roleFromGroups(groups: string[]): Role {
  if (groups.includes('DataUser')) return 'DataUser'
  if (groups.includes('BusinessUser')) return 'BusinessUser'
  return 'DataUser'
}

export function login(email: string, password: string): Promise<AuthUser> {
  if (config.devAuth) {
    const role: Role = email.toLowerCase().includes('business') ? 'BusinessUser' : 'DataUser'
    const user: AuthUser = {
      email,
      sub: `dev-${role.toLowerCase()}`,
      role,
      token: 'dev-token',
    }
    localStorage.setItem('clouddq_dev_user', JSON.stringify(user))
    return Promise.resolve(user)
  }

  const userPool = pool()
  if (!userPool) {
    return Promise.reject(new Error('Cognito is not configured. Set VITE_COGNITO_* or VITE_DEV_AUTH=1'))
  }

  const cognitoUser = new CognitoUser({ Username: email, Pool: userPool })
  const authDetails = new AuthenticationDetails({ Username: email, Password: password })

  return new Promise((resolve, reject) => {
    cognitoUser.authenticateUser(authDetails, {
      onSuccess: (session) => {
        const groups = groupsFromSession(session)
        resolve({
          email,
          sub: session.getIdToken().payload.sub as string,
          role: roleFromGroups(groups),
          token: session.getIdToken().getJwtToken(),
        })
      },
      onFailure: (err) => reject(err),
      newPasswordRequired: () => {
        reject(new Error('New password required — set permanent password in Cognito console'))
      },
    })
  })
}

export function logout(): void {
  localStorage.removeItem('clouddq_dev_user')
  const userPool = pool()
  const current = userPool?.getCurrentUser()
  current?.signOut()
}

export function getCurrentUser(): Promise<AuthUser | null> {
  if (config.devAuth) {
    const raw = localStorage.getItem('clouddq_dev_user')
    return Promise.resolve(raw ? (JSON.parse(raw) as AuthUser) : null)
  }

  const userPool = pool()
  if (!userPool) return Promise.resolve(null)
  const cognitoUser = userPool.getCurrentUser()
  if (!cognitoUser) return Promise.resolve(null)

  return new Promise((resolve) => {
    cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
      if (err || !session?.isValid()) {
        resolve(null)
        return
      }
      const email =
        (session.getIdToken().payload.email as string) ||
        cognitoUser.getUsername()
      resolve({
        email,
        sub: session.getIdToken().payload.sub as string,
        role: roleFromGroups(groupsFromSession(session)),
        token: session.getIdToken().getJwtToken(),
      })
    })
  })
}

/** Optional signup helper for demo provisioning scripts. */
export function signUp(email: string, password: string): Promise<void> {
  const userPool = pool()
  if (!userPool) return Promise.reject(new Error('Cognito not configured'))
  return new Promise((resolve, reject) => {
    userPool.signUp(
      email,
      password,
      [new CognitoUserAttribute({ Name: 'email', Value: email })],
      [],
      (err) => (err ? reject(err) : resolve()),
    )
  })
}

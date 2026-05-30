# OAuth Setup Guide (GitHub + Google)

## GitHub OAuth

1. Go to: https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in:
   - Application name: `CodeGuard AI`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
4. Click "Register application"
5. Copy the Client ID
6. Click "Generate a new client secret" and copy that too

## Google OAuth

1. Go to: https://console.cloud.google.com/apis/credentials
2. Create a project, or select an existing one
3. Configure the "OAuth consent screen" (External in test mode is fine)
4. "Create Credentials" → "OAuth 2.0 Client IDs"
5. Application type: `Web application`
6. Add this under Authorized redirect URIs:
   `http://localhost:8000/api/v1/auth/google/callback`
7. Copy the Client ID and Client Secret

## Fill In backend/.env

```
GITHUB_CLIENT_ID="paste_github_client_id_here"
GITHUB_CLIENT_SECRET="paste_github_client_secret_here"

GOOGLE_CLIENT_ID="paste_google_client_id_here"
GOOGLE_CLIENT_SECRET="paste_google_client_secret_here"
```

## Restart The Backend

```bash
cd codeguard-ai/backend
# Windows:
start.bat
```

Done. The GitHub and Google buttons on the Login/Signup pages will enable automatically.

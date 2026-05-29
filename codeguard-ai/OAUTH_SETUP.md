# OAuth Setup Guide (GitHub + Google)

## GitHub OAuth

1. Ja: https://github.com/settings/developers
2. "New OAuth App" click karo
3. Fill karo:
   - Application name: `CodeGuard AI`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
4. "Register application" karo
5. Client ID copy karo
6. "Generate a new client secret" karo aur woh bhi copy karo

## Google OAuth

1. Ja: https://console.cloud.google.com/apis/credentials
2. Project banao (ya existing select karo)
3. "OAuth consent screen" configure karo (External, test mode theek hai)
4. "Create Credentials" → "OAuth 2.0 Client IDs"
5. Application type: `Web application`
6. Authorized redirect URIs mein add karo:
   `http://localhost:8000/api/v1/auth/google/callback`
7. Client ID aur Client Secret copy karo

## backend/.env mein fill karo

```
GITHUB_CLIENT_ID="paste_github_client_id_here"
GITHUB_CLIENT_SECRET="paste_github_client_secret_here"

GOOGLE_CLIENT_ID="paste_google_client_id_here"
GOOGLE_CLIENT_SECRET="paste_google_client_secret_here"
```

## Backend restart karo

```bash
cd codeguard-ai/backend
# Windows:
start.bat
```

Bas! Login/Signup page pe GitHub aur Google buttons automatically enable ho jayenge.

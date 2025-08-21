# Deployment Guide

This guide will help you set up automatic testing and deployment to Fly.io using GitHub Actions.

## Prerequisites

1. **GitHub Repository**: Your code should be pushed to GitHub
2. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
3. **Fly CLI**: Install the Fly CLI locally for initial setup

## Step 1: Set up Fly.io Application

### Install Fly CLI
```bash
# macOS
brew install flyctl

# Or download from https://fly.io/docs/hands-on/install-flyctl/
```

### Login to Fly.io
```bash
fly auth login
```

### Create a new Fly.io app
```bash
fly apps create tdg-mvp
```

### Initialize Fly.io configuration
```bash
fly launch --no-deploy
```

This will create a `fly.toml` file. Make sure it looks like this:

```toml
app = "tdg-mvp"
primary_region = "iad"

[build]

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

## Step 2: Configure GitHub Secrets

Go to your GitHub repository: `https://github.com/masseyis/tdg/settings/secrets/actions`

Add the following secrets:

### FLY_API_TOKEN
1. Generate a Fly.io API token:
   ```bash
   fly tokens create deploy
   ```
2. Copy the token and add it as `FLY_API_TOKEN` in GitHub secrets

### FLY_APP_URL (Optional)
Add your Fly.io app URL as `FLY_APP_URL`:
```
https://tdg-mvp.fly.dev
```

## Step 3: Test the Pipeline

### Local Testing
Before pushing to GitHub, test locally:

```bash
# Run the CI tests locally
make test-ci

# Test the application
make dev
```

### Push to GitHub
The CI/CD pipeline will automatically run when you push to the `main` branch:

```bash
git push origin main
```

## Step 4: Monitor the Pipeline

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. You should see the workflows running:
   - **Test Suite**: Runs Python tests, Java tests, and integration tests
   - **Deploy to Fly.io**: Deploys to Fly.io after successful tests

## Step 5: Verify Deployment

Once the deployment is complete, your app will be available at:
```
https://tdg-mvp.fly.dev
```

Test the health endpoint:
```bash
curl https://tdg-mvp.fly.dev/health
```

## Workflow Overview

### Test Suite Workflow (`.github/workflows/test-suite.yml`)
- **Python Tests**: Runs pytest with coverage
- **Java Tests**: Generates and runs Java test cases
- **Integration Tests**: Tests the running application
- **Code Quality**: Runs flake8 and black checks

### Deployment Workflow (`.github/workflows/deploy.yml`)
- **Trigger**: Runs after successful Test Suite completion
- **Deployment**: Deploys to Fly.io using flyctl
- **Health Check**: Verifies the deployment is working

## Troubleshooting

### Common Issues

1. **Tests Fail**: Check the Actions tab for detailed error messages
2. **Deployment Fails**: Verify your `FLY_API_TOKEN` is correct
3. **App Not Starting**: Check the Fly.io logs: `fly logs`

### Local Debugging

```bash
# Run tests locally
make test-ci

# Start the app locally
make dev

# Check Fly.io status
fly status

# View Fly.io logs
fly logs
```

### Environment Variables

Make sure your `.env` file (not committed to git) contains:
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
APP_SECRET=your_secret_key
```

## Advanced Configuration

### Custom Domains
To use a custom domain:
```bash
fly certs add your-domain.com
```

### Scaling
To scale your application:
```bash
fly scale count 2
```

### Monitoring
View metrics in the Fly.io dashboard or use:
```bash
fly status
fly logs
```

## Security Notes

- Never commit API keys or secrets to git
- Use GitHub secrets for sensitive configuration
- The `.env.example` file contains placeholders only
- Production deployments should use proper secrets management

## Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Review Fly.io documentation: https://fly.io/docs/
3. Check the application logs: `fly logs`

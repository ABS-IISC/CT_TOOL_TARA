# Deployment Guide

## Railway Deployment

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the configuration from `railway.json` and `Procfile`
3. Deploy with one click

**Files used:** `railway.json`, `Procfile`, `nixpacks.toml`

## Docker Deployment

### Local Docker
```bash
docker build -t ct-review-tool .
docker run -p 5000:5000 ct-review-tool
```

### Docker Compose
```bash
docker-compose up -d
```

**Files used:** `Dockerfile`, `docker-compose.yml`

## EC2 Deployment

1. Launch Ubuntu EC2 instance
2. Copy and run the setup script:
```bash
curl -O https://raw.githubusercontent.com/ABS-IISC/CT_TOOL/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh
```

**Files used:** `ec2-setup.sh`

## Environment Variables

Set these for production deployments:
- `PORT`: Application port (auto-detected for Railway)
- `FLASK_ENV`: Set to 'production'
- `AWS_ACCESS_KEY_ID`: For AWS Bedrock (optional)
- `AWS_SECRET_ACCESS_KEY`: For AWS Bedrock (optional)
- `AWS_DEFAULT_REGION`: AWS region (optional)
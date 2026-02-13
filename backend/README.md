---
title: SentinelAI Backend
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# SentinelAI Backend

This is the backend for the SentinelAI Insider Threat Detection System.

## Environment Variables

Make sure to set the following secrets in your Space settings:

- `MONGODB_URL`: Your MongoDB connection string.
- `SECRET_KEY`: Your secret key for JWT.
- `ALGORITHM`: (Optional, default HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: (Optional)

## API Documentation

Once running, the API docs will be available at `/docs`.

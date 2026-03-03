# GitHub-Follower-Bots

A Collection of GitHub Bots for Automated Following

## Overview

This repo is a collection of automation scripts designed to manage GitHub follow interactions efficiently.

Currently, the repository includes:

- **Follow Back Bot** – Automatically follows users who follow your GitHub account.

More automation bots may be added in future updates.


## Bots

### Follow Back Bot
- Automatically follows back followers

## Requirements

- Python 3.14+
- GitHub Personal Access Token (PAT)

## How to use
### Set Personal Access Token
- Windows
```powershell
$env:GITHUB_TOKEN="your_token"
```
- Mac or Linux
```bash
export GITHUB_TOKEN="your_token"
```

### Execute Follow-Back-Bot
```powershell
python3 follow_back.py --check
```

# iTaK Deployment Checklist

Quick reference checklist for deploying iTaK to different environments.

---

## 🚀 Development/Testing Environment

**Time Required:** 10-15 minutes  
**Use Case:** Local testing, development, experimentation

### Prerequisites
- [ ] Python 3.11+ installed (`python --version`)
- [ ] pip installed (`pip --version`)
- [ ] Git installed (`git --version`)

### Setup Steps

1. **Install Dependencies**
   ```bash
   cd iTaK
   pip install -r install/requirements/requirements.txt
   ```

2. **Configure**
   ```bash
   cp install/config/config.json.example config.json
   cp install/config/.env.example .env
   ```

3. **Add API Key** (pick one)
   ```bash
   # Edit .env and add:
   GOOGLE_API_KEY=your_key_here
   # OR
   OPENAI_API_KEY=your_key_here
   ```

4. **Verify Setup**
   ```bash
   python -m app.main --doctor
   ```
   - [ ] All critical checks pass (some warnings are OK)
   - [ ] At least one LLM provider configured

5. **Test Run**
   ```bash
   # CLI only
   python -m app.main
   
   # With WebUI
   python -m app.main --webui
   ```
   - [ ] Application starts without errors
   - [ ] Can send messages and get responses
   - [ ] WebUI accessible at http://localhost:48920 (if enabled)

---

## 🏢 Team/Staging Environment

**Time Required:** 30-60 minutes  
**Use Case:** Team collaboration, shared instance, staging environment

### Additional Prerequisites
- [ ] Docker installed (`docker --version`)
- [ ] docker compose installed (`docker compose version`)

### Setup Steps

1. **Complete Development Setup** (above)

2. **Security Hardening**
   ```bash
   # Generate strong auth token
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Add to config.json
   {
     "webui": {
       "auth_token": "paste-generated-token-here"
     }
   }
   ```
   - [ ] WebUI auth token set
   - [ ] MCP auth token set (if using MCP server)

3. **Configure Rate Limits**
   ```json
   // In config.json
   {
     "security": {
       "rate_limit": {
         "global_rpm": 60,
         "per_user_rpm": 20
       }
     }
   }
   ```
   - [ ] Rate limits reviewed and adjusted
   - [ ] Tool-specific limits configured

4. **Set Up Optional Services** (as needed)
   ```bash
   # Start full stack with Docker
   docker compose --project-directory . -f install/docker/docker-compose.yml up -d
   ```
   - [ ] Neo4j running (if needed)
   - [ ] Weaviate running (if needed)
   - [ ] SearXNG running (if needed)

5. **Configure Adapters** (optional)
   ```bash
   # Add to .env
   DISCORD_TOKEN=your_discord_bot_token
   TELEGRAM_TOKEN=your_telegram_bot_token
   SLACK_TOKEN=your_slack_bot_token
   ```
   - [ ] Discord adapter configured (if needed)
   - [ ] Telegram adapter configured (if needed)
   - [ ] Slack adapter configured (if needed)

6. **Test Multi-User Access**
   - [ ] Create test users
   - [ ] Verify RBAC permissions (owner/sudo/user)
   - [ ] Test concurrent access

7. **Set Up Monitoring**
   - [ ] Review logs in `logs/` directory
   - [ ] Set up log rotation
   - [ ] Configure alerts for critical errors

---

## 🌐 Production Environment

**Time Required:** 4-8 hours  
**Use Case:** Public deployment, production workloads

### ⚠️ WARNING
iTaK executes arbitrary code by design. Only deploy to production if:
- You understand the security implications
- Access is restricted to trusted users
- You have proper monitoring and incident response

### Additional Prerequisites
- [ ] HTTPS/TLS certificate
- [ ] Reverse proxy (nginx/caddy/traefik)
- [ ] Monitoring system (Prometheus/Grafana/Datadog)
- [ ] Backup solution
- [ ] Firewall configured

### Setup Steps

1. **Complete Team/Staging Setup** (above)

2. **Infrastructure Security**
   - [ ] Set up HTTPS with valid TLS certificate
   - [ ] Configure reverse proxy
   - [ ] Set up firewall rules
   - [ ] Enable fail2ban or similar
   - [ ] Configure DDoS protection

3. **Application Security**
   - [ ] Change all default passwords and tokens
   - [ ] Review and minimize tool permissions
   - [ ] Enable output guard for PII/secret redaction
   - [ ] Test SSRF protection
   - [ ] Test path traversal protection
   - [ ] Review and tighten rate limits

4. **Production Configuration**
   ```json
   // config.json - production settings
   {
     "agent": {
       "max_iterations": 30,  // Limit loop iterations
       "timeout_seconds": 300  // Prevent infinite loops
     },
     "security": {
       "rate_limit": {
         "global_rpm": 120,
         "per_user_rpm": 10,
         "per_tool": {
           "code_execution": 5,
           "web_search": 20
         }
       }
     },
     "output_guard": {
       "enabled": true,
       "strict_mode": true,
       "log_redactions": true
     }
   }
   ```
   - [ ] Iteration limits set
   - [ ] Timeouts configured
   - [ ] Strict output guard enabled
   - [ ] Conservative rate limits

5. **Database & Persistence**
   ```bash
   # Set up production databases
   docker compose -f docker-compose.prod.yml up -d
   ```
   - [ ] Neo4j configured with persistent volume
   - [ ] Weaviate configured with persistent volume
   - [ ] SQLite data directory backed up regularly
   - [ ] Database credentials rotated from defaults

6. **Monitoring & Alerting**
   - [ ] CPU/memory monitoring
   - [ ] Disk space alerts
   - [ ] Error rate alerts
   - [ ] API cost monitoring
   - [ ] Log aggregation (ELK/Loki/CloudWatch)
   - [ ] Uptime monitoring

7. **Backup & Recovery**
   - [ ] Daily backups of `data/` directory
   - [ ] Database backup strategy
   - [ ] Disaster recovery plan documented
   - [ ] Recovery procedure tested

8. **Testing**
   - [ ] Full test suite passes: `pytest tests/ -v`
   - [ ] Security scan clean: `python -m app.main --doctor`
   - [ ] Load testing completed
   - [ ] Failover testing completed
   - [ ] Backup restore tested

9. **Documentation**
   - [ ] Runbook created
   - [ ] Incident response plan
   - [ ] User access procedures
   - [ ] Maintenance procedures
   - [ ] Contact information for on-call

10. **Legal & Compliance**
    - [ ] Terms of service reviewed
    - [ ] Privacy policy updated
    - [ ] GDPR compliance checked (if applicable)
    - [ ] AI usage disclosures
    - [ ] Liability reviewed with legal team

---

## 🐳 Docker Deployment

### Quick Start
```bash
# Development
docker compose --project-directory . -f install/docker/docker-compose.yml up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

### Verification
```bash
# Check container status
docker compose --project-directory . -f install/docker/docker-compose.yml ps

# View logs
docker compose --project-directory . -f install/docker/docker-compose.yml logs -f itak

# Run diagnostics inside container
docker compose --project-directory . -f install/docker/docker-compose.yml exec itak python -m app.main --doctor

# Restart services
docker compose --project-directory . -f install/docker/docker-compose.yml restart
```

---

## 📊 Health Checks

Run these regularly to ensure system health:

### Daily
```bash
# Check service status
python -m app.main --doctor

# Review error logs
tail -n 100 logs/errors.log

# Check disk space
df -h data/
```

### Weekly
```bash
# Run test suite
pytest tests/ -v

# Review API costs
# Check logs for cost_usd entries

# Database integrity
sqlite3 data/db/logs.db "PRAGMA integrity_check;"
```

### Monthly
```bash
# Rotate API keys
# Update dependencies: pip install -r install/requirements/requirements.txt --upgrade
# Update dependencies: pip install -r install/requirements/requirements.txt --upgrade
# Review and archive old logs
# Test backup restore procedure
```

---

## 🆘 Troubleshooting

### Application won't start
1. Run `python -m app.main --doctor`
2. Check for missing dependencies
3. Verify API keys in `.env`
4. Check config.json syntax

### WebUI not accessible
1. Check if port 48920 is open
2. Verify auth token is correct
3. Check firewall rules
4. Review webui logs

### Agent not responding
1. Check LLM API key is valid
2. Verify API rate limits not exceeded
3. Check network connectivity
4. Review agent logs for errors

### High API costs
1. Review rate limits
2. Check for infinite loops (max_iterations)
3. Monitor token usage in logs
4. Consider switching to cheaper models

### Memory issues
1. Check SQLite database size
2. Archive old logs
3. Optimize Neo4j/Weaviate if used
4. Review memory retention settings

---

## 📞 Support

- **Documentation:** `docs/` directory
- **Issues:** https://github.com/David2024patton/iTaK/issues
- **Diagnostics:** `python -m app.main --doctor`
- **Tests:** `pytest tests/ -v --tb=short`

---

**Last Updated:** 2026-02-14  
**Version:** 4.0

# Test Incident Logs for SRE Assistant

Implement as tests later

## 1. CI/CD Pipeline Failure
```
Jenkins pipeline failed at 14:23 UTC during deployment to production. 
Error: "fatal: unable to access 'https://gitlab.com/project/repo.git/': The requested URL returned error: 403"
Git authentication seems to be failing. Pipeline was working fine yesterday.
Affecting: All deployments to prod environment
Status: Critical - blocking all releases
```

## 2. Database Connection Issues
```
Application experiencing intermittent 500 errors starting at 09:45 UTC.
Database connection pool exhausted - "HikariPool-1 - Connection is not available, request timed out after 30000ms"
CPU usage on DB server spiked to 95%. Several long-running queries detected.
Users reporting slow page loads and timeouts on checkout flow.
Status: High - impacting user experience
```

## 3. Kubernetes Pod Crashes
```
Production API pods crashing with OOMKilled status since 11:30 UTC.
Memory usage pattern shows gradual increase over 6 hours before crash.
Error logs show: "java.lang.OutOfMemoryError: Java heap space"
Pod restarts are happening every 20-30 minutes.
Traffic levels appear normal - no unusual load spikes detected.
```

## 4. SSL Certificate Expiry
```
Website showing "Your connection is not private" error as of 06:00 UTC.
SSL certificate for *.company.com expired at 05:59 UTC.
Cert-manager automatic renewal appears to have failed.
Error in cert-manager logs: "ACME challenge failed - DNS propagation timeout"
All HTTPS traffic affected across multiple subdomains.
```

## 5. Network Connectivity Issues
```
Intermittent connectivity issues between microservices in us-east-1 region.
Service mesh reporting 15% of requests failing with connection timeouts.
AWS status page shows no reported issues.
Istio proxy logs showing: "upstream connect error or disconnect/reset before headers"
Latency increased from 50ms to 800ms average for inter-service calls.
```

## 6. Storage Space Exhaustion
```
Application logs stopped writing at 13:45 UTC.
Disk usage on /var partition reached 100% capacity.
Log rotation appears to have failed - found logs from 6 months ago still present.
Application container unable to write temporary files.
Error: "No space left on device" appearing in multiple services.
```

## 7. Load Balancer Misconfiguration
```
Traffic not routing properly to new deployment after blue-green switch.
ALB showing 502 Bad Gateway errors for 30% of requests.
Health checks passing but application returning connection refused.
Target group shows healthy targets but traffic distribution uneven.
Started after deployment of v2.1.4 at 16:20 UTC.
```

## 8. Redis Cache Failure
```
Application performance degraded significantly since 12:00 UTC.
Redis cluster showing "CLUSTERDOWN The cluster is down" error.
Page load times increased from 200ms to 3-4 seconds.
Database query volume increased 10x due to cache misses.
Redis master election appears to be failing repeatedly.
```

## 9. Container Registry Issues
```
Docker builds failing with "pull access denied" errors since 08:30 UTC.
Base image pulls timing out from Docker Hub.
CI/CD pipeline stuck at image pull stage.
Error: "toomanyrequests: You have reached your pull rate limit"
Affecting all builds across multiple projects and environments.
```

## 10. Monitoring Alert Storm
```
PagerDuty receiving 200+ alerts per minute starting 07:15 UTC.
Prometheus targets showing as "down" despite services being healthy.
Grafana dashboards showing no data for past 2 hours.
Alert manager appears to be in a loop sending duplicate notifications.
Monitoring infrastructure consuming high CPU and memory.
```

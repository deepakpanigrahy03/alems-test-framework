# Add to crontab (run: crontab -e)
# Runs health check daily at 06:00.
#
# 0 6 * * * cd ~/mydrive/alems-test-framework && \
#   python checks/tier_d/health_check.py --machine gn100-2b96 \
#   >> ~/mydrive/alems-test-framework/reports/health/cron.log 2>&1

Sidekiq.configure_server do |config|
  config.redis = { url: ENV.fetch("REDIS_URL", "redis://localhost:6379/0") }

  Sidekiq::Cron::Job.load_from_hash(
    "daily_automation" => {
      "cron"        => "0 9 * * *",
      "class"       => "DailyAutomationJob",
      "queue"       => "automation",
      "description" => "Search and apply to top 10 jobs per active user"
    },
    "retry_failed_applications" => {
      "cron"        => "*/30 * * * *",
      "class"       => "RetryFailedApplicationsJob",
      "queue"       => "automation",
      "description" => "Retry failed applications (max 3 retries)"
    },
    "llm_quota_init" => {
      "cron"        => "5 0 * * *",
      "class"       => "LlmQuotaInitJob",
      "queue"       => "default",
      "description" => "Ensure today's LLM quota row exists"
    }
  )
end

Sidekiq.configure_client do |config|
  config.redis = { url: ENV.fetch("REDIS_URL", "redis://localhost:6379/0") }
end

class RetryFailedApplicationsJob
  include Sidekiq::Job
  sidekiq_options queue: "automation", retry: 2

  def perform
    if LlmApiUsage.quota_exceeded?
      Rails.logger.warn("RetryFailedApplicationsJob: LLM quota exceeded, skipping retries.")
      return
    end

    Application.failed_retryable.includes(:user).find_each do |app|
      AgentDispatcher.dispatch_retry(app.user_id, app.id)
      app.increment!(:retry_count)
      Rails.logger.info("RetryFailedApplicationsJob: dispatched retry for application #{app.id}")
    end
  end
end

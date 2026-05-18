class LlmQuotaInitJob
  include Sidekiq::Job
  sidekiq_options queue: "default"

  def perform
    LlmApiUsage.find_or_create_by(date: Date.current)
    Rails.logger.info("LlmQuotaInitJob: ensured quota row for #{Date.current}")
  end
end

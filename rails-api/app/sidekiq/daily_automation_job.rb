class DailyAutomationJob
  include Sidekiq::Job
  sidekiq_options queue: "automation", retry: 3

  def perform
    if LlmApiUsage.quota_exceeded?
      Rails.logger.warn("DailyAutomationJob: LLM quota already exceeded for #{Date.current}, skipping.")
      return
    end

    User.where(active: true).find_each do |user|
      AgentDispatcher.dispatch_run(user.id)
      Rails.logger.info("DailyAutomationJob: dispatched run for user #{user.id}")
    end
  end
end

class DashboardController < WebController
  def index
    @stats = ::Application::STATUSES.index_with { |s| @current_user.applications.where(status: s).count }
    limit = ENV.fetch("MAX_LLM_API_CALLS_PER_DAY", "200").to_i
    used = LlmApiUsage.where(date: Date.current).pick(:api_calls_count) || 0
    @llm = { used: used, limit: limit }
    @recent = @current_user.applications.includes(:job).order(created_at: :desc).limit(10)
  end

  def start_automation
    if LlmApiUsage.quota_exceeded?
      redirect_to root_path, alert: "Daily LLM quota exceeded."
    else
      AgentDispatcher.dispatch_run(@current_user.id)
      redirect_to root_path, notice: "Automation started."
    end
  end
end

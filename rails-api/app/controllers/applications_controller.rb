class ApplicationsController < WebController
  def index
    @applications = @current_user.applications.includes(:job).order(created_at: :desc).limit(100)
  end

  def show
    @application = @current_user.applications.includes(:job, :automation_logs).find(params[:id])
  end

  def retry
    app = @current_user.applications.find(params[:id])
    if app.retry_count >= 3
      redirect_to application_path(app), alert: "Max retries (3) already reached."
    else
      AgentDispatcher.dispatch_retry(@current_user.id, app.id)
      app.update!(status: "pending")
      redirect_to application_path(app), notice: "Retry queued."
    end
  end
end

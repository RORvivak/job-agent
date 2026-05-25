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

  def mark_applied
    app = @current_user.applications.find(params[:id])
    app.update!(status: "applied", applied_at: Time.current)
    redirect_to root_path, notice: "Marked as applied."
  end

  def download_resume
    app = @current_user.applications.find(params[:id])
    if app.resume_file.attached?
      redirect_to rails_blob_path(app.resume_file, disposition: "attachment")
    else
      redirect_to root_path, alert: "No resume available."
    end
  end

  def download_cover_letter
    app = @current_user.applications.find(params[:id])
    if app.cover_letter_file.attached?
      redirect_to rails_blob_path(app.cover_letter_file, disposition: "attachment")
    else
      redirect_to root_path, alert: "No cover letter available."
    end
  end
end

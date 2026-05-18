module Api
  module V1
    class ApplicationsController < BaseController
      def index
        apps = @current_user.applications
          .includes(:job, :automation_logs)
          .order(created_at: :desc)
          .limit(100)

        render json: apps.map { |a|
          {
            id: a.id,
            status: a.status,
            applied_at: a.applied_at,
            retry_count: a.retry_count,
            job: { id: a.job.id, title: a.job.title, company: a.job.company, portal: a.job.portal, url: a.job.job_url },
            error_message: a.error_message,
            screenshot_path: a.screenshot_path
          }
        }
      end

      def show
        app = @current_user.applications.includes(:job).find(params[:id])
        render json: {
          id: app.id,
          status: app.status,
          applied_at: app.applied_at,
          retry_count: app.retry_count,
          resume_path: app.resume_path,
          cover_letter_path: app.cover_letter_path,
          error_message: app.error_message,
          screenshot_path: app.screenshot_path,
          job: { id: app.job.id, title: app.job.title, company: app.job.company, portal: app.job.portal, url: app.job.job_url, description: app.job.description },
        }
      end

      def retry
        app = @current_user.applications.find(params[:id])
        return render json: { error: "Max retries reached" }, status: :unprocessable_entity if app.retry_count >= 3

        correlation_id = AgentDispatcher.dispatch_retry(@current_user.id, app.id)
        app.update!(status: "pending")
        render json: { retried: true, correlation_id: }
      end
    end
  end
end

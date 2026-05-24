module Api
  module V1
    class AgentCallbackController < ApplicationController
      before_action :verify_agent_jwt

      def create
        event = params[:event]
        app_id = params[:application_id]
        correlation_id = params[:correlation_id]

        case event
        when "log"
          application = Application.find_by(id: app_id)
          if application
            AutomationLog.create!(
              application: application,
              step: params[:step],
              status: params[:status],
              message: params[:message]
            )
          end
        when "status_update"
          application = Application.find_by(id: app_id)
          attrs = {
            status: params[:status],
            error_message: params[:error_message],
            screenshot_path: params[:screenshot_path],
            failed_step: params[:failed_step],
          }
          attrs[:applied_at] = params[:applied_at] if params[:applied_at].present?
          application&.update!(attrs)
        when "llm_usage"
          LlmApiUsage.increment_today!(by: params[:count].to_i)
        when "upsert_job"
          job = Job.find_or_initialize_by(portal: params[:portal], job_url: params[:job_url])
          job.update!(
            title: params[:title],
            company: params[:company],
            description: params[:description],
            relevance_score: params[:relevance_score].to_f
          )
        when "create_application"
          job = Job.find_or_initialize_by(portal: params[:portal], job_url: params[:job_url])
          job.update!(
            title: params[:title],
            company: params[:company],
            description: params[:description].to_s,
            relevance_score: params[:relevance_score].to_f
          )
          user = User.find(params[:user_id])
          application = user.applications.find_or_initialize_by(job: job)
          application.update!(status: "running", correlation_id: params[:correlation_id])
          return render json: { ok: true, application_id: application.id }
        end

        REDIS.with { |r| r.publish("agent:progress:#{correlation_id}", params.to_json) } if correlation_id

        render json: { ok: true }
      end

      private

      def verify_agent_jwt
        token = request.headers["Authorization"]&.split(" ")&.last
        claims = AgentJwt.decode(token)
        head :unauthorized unless claims
      end
    end
  end
end

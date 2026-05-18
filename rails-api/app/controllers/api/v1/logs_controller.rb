module Api
  module V1
    class LogsController < BaseController
      def index
        logs = AutomationLog.joins(application: :user)
          .where(users: { id: @current_user.id })
          .order(created_at: :desc)
          .limit(200)

        render json: logs.map { |l|
          { id: l.id, application_id: l.application_id, step: l.step, status: l.status, message: l.message, created_at: l.created_at }
        }
      end
    end
  end
end

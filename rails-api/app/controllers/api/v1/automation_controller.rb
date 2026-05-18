module Api
  module V1
    class AutomationController < BaseController
      def start
        user = @current_user
        if LlmApiUsage.quota_exceeded?
          return render json: { error: "Daily LLM API limit reached. Automation stopped." }, status: :too_many_requests
        end

        correlation_id = AgentDispatcher.dispatch_run(user.id)
        render json: { started: true, correlation_id: }
      end
    end
  end
end

module Api
  module V1
    class LlmUsagesController < BaseController
      def index
        limit = ENV.fetch("MAX_LLM_API_CALLS_PER_DAY", "200").to_i
        used = LlmApiUsage.where(date: Date.current).pick(:api_calls_count) || 0
        render json: {
          date: Date.current,
          limit:,
          used:,
          remaining: limit - used,
          quota_exceeded: used >= limit
        }
      end
    end
  end
end

class AgentDispatcher
  TYPE_RUN   = "run_automation".freeze
  TYPE_RETRY = "retry_application".freeze

  def self.dispatch_run(user_id, preference_ids: nil)
    push(type: TYPE_RUN, user_id:, preference_ids:)
  end

  def self.dispatch_retry(user_id, application_id)
    push(type: TYPE_RETRY, user_id:, application_id:)
  end

  private

  def self.push(type:, **kwargs)
    correlation_id = SecureRandom.uuid
    payload = {
      type:,
      correlation_id:,
      enqueued_at: Time.current.iso8601,
      jwt: AgentJwt.encode({ user_id: kwargs[:user_id] }),
      **kwargs
    }
    queue = ENV.fetch("JOB_QUEUE_NAME", "job_queue")
    REDIS.with { |r| r.lpush(queue, payload.to_json) }
    correlation_id
  end
end

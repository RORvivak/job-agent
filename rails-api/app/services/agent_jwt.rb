class AgentJwt
  SECRET = ENV.fetch("AGENT_SHARED_SECRET", "change_me")
  ALGORITHM = "HS256".freeze

  def self.encode(payload)
    JWT.encode(payload.merge(exp: 1.hour.from_now.to_i), SECRET, ALGORITHM)
  end

  def self.decode(token)
    JWT.decode(token, SECRET, true, { algorithm: ALGORITHM }).first
  rescue JWT::DecodeError
    nil
  end
end

class LlmApiUsage < ApplicationRecord
  validates :date, presence: true, uniqueness: true

  def self.increment_today!(by: 1)
    row = find_or_create_by(date: Date.current)
    row.with_lock { row.increment!(:api_calls_count, by) }
    row
  end

  def self.quota_remaining
    limit = ENV.fetch("MAX_LLM_API_CALLS_PER_DAY", "200").to_i
    used = where(date: Date.current).pick(:api_calls_count) || 0
    limit - used
  end

  def self.quota_exceeded?
    quota_remaining <= 0
  end
end

class Application < ApplicationRecord
  belongs_to :user
  belongs_to :job
  has_many :automation_logs, dependent: :destroy

  STATUSES = %w[pending running applied failed paused_quota paused_captcha skipped].freeze

  validates :status, inclusion: { in: STATUSES }

  scope :failed_retryable, -> {
    where(status: "failed").where("retry_count < ?", 3)
  }
end

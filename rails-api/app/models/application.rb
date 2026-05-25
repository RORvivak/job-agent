class Application < ApplicationRecord
  belongs_to :user
  belongs_to :job
  has_many :automation_logs, dependent: :destroy
  has_one_attached :resume_file
  has_one_attached :cover_letter_file

  STATUSES = %w[pending running ready_to_apply applied failed paused_quota paused_captcha skipped].freeze

  validates :status, inclusion: { in: STATUSES }

  scope :failed_retryable, -> {
    where(status: "failed").where("retry_count < ?", 3)
  }
end

class Job < ApplicationRecord
  has_many :applications, dependent: :destroy

  validates :portal, :title, :job_url, presence: true
  validates :job_url, uniqueness: { scope: :portal }
end

class AutomationLog < ApplicationRecord
  belongs_to :application

  validates :step, :status, presence: true
end

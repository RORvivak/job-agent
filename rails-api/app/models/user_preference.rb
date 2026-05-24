class UserPreference < ApplicationRecord
  belongs_to :user

  serialize :desired_roles,   coder: JSON
  serialize :preferred_stack, coder: JSON
  serialize :locations,       coder: JSON

  scope :active, -> { where(active: true) }

  validates :name, presence: true
end

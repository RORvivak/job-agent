class Resume < ApplicationRecord
  belongs_to :user

  serialize :extracted_skills, coder: JSON
  serialize :parsed_data,      coder: JSON

  scope :active, -> { where(active: true) }
end

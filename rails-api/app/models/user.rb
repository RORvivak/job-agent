class User < ApplicationRecord
  has_many :user_preferences, dependent: :destroy
  has_many :resumes, dependent: :destroy
  has_many :applications, dependent: :destroy

  validates :name, presence: true
  validates :email, presence: true, uniqueness: true

  def active_resume
    resumes.where(active: true).last
  end
end

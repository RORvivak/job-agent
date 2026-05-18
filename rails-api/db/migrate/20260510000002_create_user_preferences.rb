class CreateUserPreferences < ActiveRecord::Migration[8.1]
  def change
    create_table :user_preferences do |t|
      t.references :user, null: false, foreign_key: true
      t.text :desired_roles
      t.text :preferred_stack
      t.text :locations
      t.string :remote_preference, default: "remote"
      t.integer :salary_min
      t.integer :salary_max
      t.integer :years_experience
      t.text :additional_info
      t.timestamps
    end
  end
end

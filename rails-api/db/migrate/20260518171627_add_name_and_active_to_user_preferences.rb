class AddNameAndActiveToUserPreferences < ActiveRecord::Migration[8.1]
  def change
    add_column :user_preferences, :name, :string, default: "Default"
    add_column :user_preferences, :active, :boolean, default: true, null: false
  end
end

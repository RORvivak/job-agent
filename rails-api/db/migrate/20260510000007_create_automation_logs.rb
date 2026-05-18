class CreateAutomationLogs < ActiveRecord::Migration[8.1]
  def change
    create_table :automation_logs do |t|
      t.references :application, null: false, foreign_key: true
      t.string :step, null: false
      t.string :status, null: false
      t.text :message
      t.timestamps
    end
    add_index :automation_logs, [:application_id, :created_at]
  end
end

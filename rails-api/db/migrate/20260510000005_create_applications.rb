class CreateApplications < ActiveRecord::Migration[8.1]
  def change
    create_table :applications do |t|
      t.references :user, null: false, foreign_key: true
      t.references :job, null: false, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.datetime :applied_at
      t.string :resume_path
      t.string :cover_letter_path
      t.text :error_message
      t.string :screenshot_path
      t.integer :retry_count, default: 0
      t.string :correlation_id
      t.text :failed_step
      t.timestamps
    end
    add_index :applications, :status
    add_index :applications, :correlation_id
  end
end

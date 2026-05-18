class CreateLlmApiUsages < ActiveRecord::Migration[8.1]
  def change
    create_table :llm_api_usages do |t|
      t.date :date, null: false
      t.integer :api_calls_count, default: 0, null: false
      t.timestamps
    end
    add_index :llm_api_usages, :date, unique: true
  end
end

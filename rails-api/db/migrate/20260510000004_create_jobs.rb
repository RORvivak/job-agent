class CreateJobs < ActiveRecord::Migration[8.1]
  def change
    create_table :jobs do |t|
      t.string :portal, null: false
      t.string :company
      t.string :title, null: false
      t.text :description
      t.string :job_url, null: false
      t.float :relevance_score
      t.string :posted_at
      t.timestamps
    end
    add_index :jobs, [:portal, :job_url], unique: true
  end
end

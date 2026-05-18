class CreateResumes < ActiveRecord::Migration[8.1]
  def change
    create_table :resumes do |t|
      t.references :user, null: false, foreign_key: true
      t.string :original_resume_path
      t.string :customized_resume_path
      t.text :extracted_skills
      t.text :parsed_data
      t.boolean :active, default: true
      t.timestamps
    end
  end
end

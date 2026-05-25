# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_05_24_161347) do
  create_table "active_storage_attachments", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.datetime "created_at", null: false
    t.string "name", null: false
    t.bigint "record_id", null: false
    t.string "record_type", null: false
    t.index ["blob_id"], name: "index_active_storage_attachments_on_blob_id"
    t.index ["record_type", "record_id", "name", "blob_id"], name: "index_active_storage_attachments_uniqueness", unique: true
  end

  create_table "active_storage_blobs", force: :cascade do |t|
    t.bigint "byte_size", null: false
    t.string "checksum"
    t.string "content_type"
    t.datetime "created_at", null: false
    t.string "filename", null: false
    t.string "key", null: false
    t.text "metadata"
    t.string "service_name", null: false
    t.index ["key"], name: "index_active_storage_blobs_on_key", unique: true
  end

  create_table "active_storage_variant_records", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.string "variation_digest", null: false
    t.index ["blob_id", "variation_digest"], name: "index_active_storage_variant_records_uniqueness", unique: true
  end

  create_table "applications", force: :cascade do |t|
    t.datetime "applied_at"
    t.string "correlation_id"
    t.string "cover_letter_path"
    t.datetime "created_at", null: false
    t.text "error_message"
    t.text "failed_step"
    t.integer "job_id", null: false
    t.string "resume_path"
    t.integer "retry_count", default: 0
    t.string "screenshot_path"
    t.string "status", default: "pending", null: false
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.index ["correlation_id"], name: "index_applications_on_correlation_id"
    t.index ["job_id"], name: "index_applications_on_job_id"
    t.index ["status"], name: "index_applications_on_status"
    t.index ["user_id"], name: "index_applications_on_user_id"
  end

  create_table "automation_logs", force: :cascade do |t|
    t.integer "application_id", null: false
    t.datetime "created_at", null: false
    t.text "message"
    t.string "status", null: false
    t.string "step", null: false
    t.datetime "updated_at", null: false
    t.index ["application_id", "created_at"], name: "index_automation_logs_on_application_id_and_created_at"
    t.index ["application_id"], name: "index_automation_logs_on_application_id"
  end

  create_table "jobs", force: :cascade do |t|
    t.string "company"
    t.datetime "created_at", null: false
    t.text "description"
    t.string "job_url", null: false
    t.string "portal", null: false
    t.string "posted_at"
    t.float "relevance_score"
    t.string "title", null: false
    t.datetime "updated_at", null: false
    t.index ["portal", "job_url"], name: "index_jobs_on_portal_and_job_url", unique: true
  end

  create_table "llm_api_usages", force: :cascade do |t|
    t.integer "api_calls_count", default: 0, null: false
    t.datetime "created_at", null: false
    t.date "date", null: false
    t.datetime "updated_at", null: false
    t.index ["date"], name: "index_llm_api_usages_on_date", unique: true
  end

  create_table "resumes", force: :cascade do |t|
    t.boolean "active", default: true
    t.datetime "created_at", null: false
    t.string "customized_resume_path"
    t.text "extracted_skills"
    t.string "original_resume_path"
    t.text "parsed_data"
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.index ["user_id"], name: "index_resumes_on_user_id"
  end

  create_table "user_preferences", force: :cascade do |t|
    t.boolean "active", default: true, null: false
    t.text "additional_info"
    t.datetime "created_at", null: false
    t.text "desired_roles"
    t.text "locations"
    t.string "name", default: "Default"
    t.text "preferred_stack"
    t.string "remote_preference", default: "remote"
    t.integer "salary_max"
    t.integer "salary_min"
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.integer "years_experience"
    t.index ["user_id"], name: "index_user_preferences_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.boolean "active", default: true, null: false
    t.datetime "created_at", null: false
    t.string "email", null: false
    t.string "name", null: false
    t.datetime "updated_at", null: false
    t.index ["email"], name: "index_users_on_email", unique: true
  end

  add_foreign_key "active_storage_attachments", "active_storage_blobs", column: "blob_id"
  add_foreign_key "active_storage_variant_records", "active_storage_blobs", column: "blob_id"
  add_foreign_key "applications", "jobs"
  add_foreign_key "applications", "users"
  add_foreign_key "automation_logs", "applications"
  add_foreign_key "resumes", "users"
  add_foreign_key "user_preferences", "users"
end

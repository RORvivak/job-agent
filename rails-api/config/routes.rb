require "sidekiq/web"

Rails.application.routes.draw do
  mount Sidekiq::Web => "/sidekiq"
  get "up" => "rails/health#show", as: :rails_health_check

  root "dashboard#index"
  post "automation/start", to: "dashboard#start_automation", as: :start_automation
  resources :applications, only: [:index, :show] do
    post :retry, on: :member
    post :mark_applied, on: :member
    get  :download_resume, on: :member
    get  :download_cover_letter, on: :member
  end
  resources :resumes, only: [:index, :create, :destroy] do
    post :activate, on: :member
  end
  resources :preferences, controller: "preferences" do
    post :toggle, on: :member
  end
  get  "preferences/new",      to: "preferences#new",  as: :new_preference
  get  "preferences/:id/edit", to: "preferences#edit", as: :edit_preference

  namespace :api do
    namespace :v1 do
      post   "resumes",                    to: "resumes#create"
      get    "resumes/:id/download",       to: "resumes#download", as: :resume_download

      post   "automation/start",           to: "automation#start"

      get    "applications",                        to: "applications#index"
      get    "applications/:id",                   to: "applications#show"
      post   "applications/:id/retry",             to: "applications#retry"
      post   "applications/:id/upload_resume",     to: "applications#upload_resume"
      post   "applications/:id/upload_cover_letter", to: "applications#upload_cover_letter"

      get    "logs",                       to: "logs#index"
      get    "llm_usage",                  to: "llm_usages#index"

      get    "users/:id/preferences",      to: "users#preferences"
      get    "users/:id/active_resume",    to: "users#active_resume"
      put    "preferences",                to: "user_preferences#create_or_update"

      post   "agent/callback",             to: "agent_callback#create"
    end
  end
end

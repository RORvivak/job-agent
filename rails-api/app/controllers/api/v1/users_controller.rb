module Api
  module V1
    class UsersController < BaseController
      def preferences
        prefs = @current_user.user_preferences.active
        return render json: {}, status: :not_found if prefs.empty?

        # Merge all active preference sets — agent gets a unified view
        render json: {
          preference_sets: prefs.map { |p|
            {
              id:                p.id,
              name:              p.name,
              desired_roles:     p.desired_roles     || [],
              preferred_stack:   p.preferred_stack   || [],
              locations:         p.locations         || [],
              remote_preference: p.remote_preference,
              salary_min:        p.salary_min,
              salary_max:        p.salary_max,
              years_experience:  p.years_experience,
              additional_info:   p.additional_info,
            }
          },
          # Flat merged view for backward compatibility with current agent
          desired_roles:     prefs.flat_map { |p| p.desired_roles || [] }.uniq,
          preferred_stack:   prefs.flat_map { |p| p.preferred_stack || [] }.uniq,
          locations:         prefs.flat_map { |p| p.locations || [] }.uniq,
          remote_preference: prefs.first.remote_preference,
          salary_min:        prefs.map(&:salary_min).compact.min,
          salary_max:        prefs.map(&:salary_max).compact.max,
          years_experience:  prefs.first.years_experience,
          additional_info:   prefs.map(&:additional_info).compact.join("; "),
        }
      end

      def active_resume
        resume = @current_user.active_resume
        return render json: {}, status: :not_found unless resume

        render json: {
          id: resume.id,
          original_resume_path: resume.original_resume_path,
          customized_resume_path: resume.customized_resume_path,
          extracted_skills: resume.extracted_skills,
          parsed_data: resume.parsed_data,
        }
      end
    end
  end
end

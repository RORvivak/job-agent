module Api
  module V1
    class UsersController < BaseController
      def preferences
        pref = @current_user.user_preference
        return render json: {}, status: :not_found unless pref

        render json: {
          desired_roles: pref.desired_roles || [],
          preferred_stack: pref.preferred_stack || [],
          locations: pref.locations || [],
          remote_preference: pref.remote_preference,
          salary_min: pref.salary_min,
          salary_max: pref.salary_max,
          years_experience: pref.years_experience,
          additional_info: pref.additional_info,
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

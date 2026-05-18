module Api
  module V1
    class UserPreferencesController < BaseController
      def show
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

      def create_or_update
        pref = @current_user.user_preference || @current_user.build_user_preference
        pref.update!(preference_params)
        render json: { updated: true }
      end

      private

      def preference_params
        params.permit(
          :remote_preference, :salary_min, :salary_max, :years_experience, :additional_info,
          desired_roles: [], preferred_stack: [], locations: []
        )
      end
    end
  end
end

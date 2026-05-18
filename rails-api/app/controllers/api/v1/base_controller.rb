module Api
  module V1
    class BaseController < ApplicationController
      before_action :set_default_user

      private

      def set_default_user
        @current_user = User.first
      end
    end
  end
end

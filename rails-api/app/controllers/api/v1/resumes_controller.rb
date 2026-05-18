module Api
  module V1
    class ResumesController < BaseController
      def create
        user = @current_user
        file = params[:file]
        return render json: { error: "file required" }, status: :unprocessable_entity unless file

        dir = Rails.root.join("storage", "resumes", user.id.to_s)
        FileUtils.mkdir_p(dir)
        dest = dir.join(file.original_filename)
        FileUtils.cp(file.tempfile.path, dest)

        resume = user.resumes.create!(original_resume_path: dest.to_s)
        AgentDispatcher.dispatch_run(user.id)

        render json: { id: resume.id, path: resume.original_resume_path }, status: :created
      end

      def download
        resume = Resume.find(params[:id])
        path = resume.customized_resume_path || resume.original_resume_path
        return render json: { error: "file not found" }, status: :not_found unless path && File.exist?(path)

        send_file path, disposition: "attachment"
      end
    end
  end
end

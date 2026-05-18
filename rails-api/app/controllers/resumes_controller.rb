class ResumesController < WebController
  def index
    @resumes = @current_user.resumes.order(created_at: :desc)
  end

  def create
    file = params[:file]
    return redirect_to resumes_path, alert: "Please select a file." unless file

    ext = File.extname(file.original_filename).downcase
    unless %w[.pdf .docx].include?(ext)
      return redirect_to resumes_path, alert: "Only PDF and DOCX files are supported."
    end

    dir = Rails.root.join("storage", "resumes", @current_user.id.to_s)
    FileUtils.mkdir_p(dir)
    dest = dir.join(file.original_filename)
    FileUtils.cp(file.tempfile.path, dest)

    @current_user.resumes.create!(original_resume_path: dest.to_s)
    redirect_to resumes_path, notice: "Resume uploaded successfully."
  end
end

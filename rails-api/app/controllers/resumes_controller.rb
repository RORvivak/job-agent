class ResumesController < WebController
  before_action :set_resume, only: [:activate, :destroy]

  def index
    # Support viewing resumes for a specific user (for future multi-user)
    @selected_user = params[:user_id] ? User.find_by(id: params[:user_id]) || @current_user : @current_user
    @users   = User.all
    @resumes = @selected_user.resumes.order(created_at: :desc)
  end

  def create
    target_user = params[:user_id] ? User.find_by(id: params[:user_id]) || @current_user : @current_user
    file = params[:file]

    return redirect_to resumes_path, alert: "Please select a file." unless file

    ext = File.extname(file.original_filename).downcase
    unless %w[.pdf .docx].include?(ext)
      return redirect_to resumes_path, alert: "Only PDF and DOCX files are supported."
    end

    dir = Rails.root.join("storage", "resumes", target_user.id.to_s)
    FileUtils.mkdir_p(dir)
    dest = dir.join(file.original_filename)
    FileUtils.cp(file.tempfile.path, dest)

    # Deactivate existing resumes and set new one as active
    target_user.resumes.update_all(active: false)
    target_user.resumes.create!(original_resume_path: dest.to_s, active: true)

    redirect_to resumes_path(user_id: target_user.id), notice: "Resume uploaded and set as active."
  end

  def activate
    @resume.user.resumes.update_all(active: false)
    @resume.update!(active: true)
    redirect_to resumes_path(user_id: @resume.user_id), notice: "Resume set as active."
  end

  def destroy
    user_id = @resume.user_id
    @resume.destroy
    redirect_to resumes_path(user_id:), notice: "Resume deleted."
  end

  private

  def set_resume
    @resume = Resume.find(params[:id])
  end
end

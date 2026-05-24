class PreferencesController < WebController
  before_action :set_preference, only: [:edit, :update, :destroy, :toggle]

  def index
    @preferences = @current_user.user_preferences.order(:name)
  end

  def new
    @preference = @current_user.user_preferences.build
  end

  def create
    @preference = @current_user.user_preferences.build(preference_params)
    apply_list_params(@preference)
    if @preference.save
      flash[:notice] = "Preference set \"#{@preference.name}\" created."
      redirect_to preferences_path
    else
      flash.now[:alert] = "Failed to save."
      render :new
    end
  end

  def edit; end

  def update
    apply_list_params(@preference)
    @preference.assign_attributes(preference_params)
    if @preference.save
      flash[:notice] = "Preference set \"#{@preference.name}\" updated."
      redirect_to preferences_path
    else
      flash.now[:alert] = "Failed to save."
      render :edit
    end
  end

  def destroy
    @preference.destroy
    flash[:notice] = "Deleted."
    redirect_to preferences_path
  end

  def toggle
    @preference.update!(active: !@preference.active)
    redirect_to preferences_path
  end

  # Legacy POST /preferences — kept so existing form still works
  def show
    redirect_to preferences_path
  end

  private

  def set_preference
    @preference = @current_user.user_preferences.find(params[:id])
  end

  def preference_params
    params.permit(:name, :remote_preference, :salary_min, :salary_max, :years_experience, :additional_info, :active)
  end

  def apply_list_params(pref)
    pref.desired_roles   = parse_list(params[:desired_roles_raw])   if params[:desired_roles_raw]
    pref.preferred_stack = parse_list(params[:preferred_stack_raw]) if params[:preferred_stack_raw]
    pref.locations       = parse_list(params[:locations_raw])       if params[:locations_raw]
  end

  def parse_list(str)
    str.to_s.split(",").map(&:strip).reject(&:empty?)
  end
end

user = User.find_or_create_by(email: "vk2853@gmail.com") do |u|
  u.name = "Vivak"
end

UserPreference.find_or_create_by(user: user) do |p|
  p.desired_roles = ["Senior Backend Engineer", "AI Engineer", "Ruby on Rails Engineer"]
  p.preferred_stack = ["Ruby on Rails", "Python", "LangGraph", "Elasticsearch", "Distributed Systems"]
  p.locations = ["Remote", "San Francisco", "New York"]
  p.remote_preference = "remote"
  p.salary_min = 150_000
  p.salary_max = 250_000
  p.years_experience = 8
end

puts "Seeded user: #{user.email} (id: #{user.id})"

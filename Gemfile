source "https://rubygems.org"

gem 'github-pages'
# this gem provides regeneration support improvements on Windows
gem 'wdm', '>= 0.1.1' if Gem.win_platform?

# Windows and JRuby does not include zoneinfo files, so bundle the tzinfo-data gem
# and associated library.
platforms :mingw, :x64_mingw, :mswin, :jruby do
    gem "tzinfo", "~> 1.2"
    gem "tzinfo-data"
  end
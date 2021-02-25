#!/usr/bin/env ruby
PAGETITLE = "Public Datafiles And Dependencies" # Wvisible:tools data

$LOAD_PATH.unshift '/srv/whimsy/lib'
require 'json'

# Command line use: emit replacement for www/public/README.html
#   Centralize maintenance of descriptions
DATAFLOWDATA = File.join(File.dirname(__FILE__), 'dataflow.json')
DATAFLOWDOC = 'https://whimsy.apache.org/test/dataflow.cgi#'
deplist = JSON.parse(File.read(DATAFLOWDATA))
README = '/srv/whimsy/www/public/README.html'

# Command line outputs to stdout raw HTML for README.html
unless ENV['SCRIPT_NAME']
  File.open(README,'w') do |out|
    out.puts %Q|<h2>Public JSON files</h2><dl>|
    out.puts %Q|<!-- DO NOT EDIT THIS FILE - manually regenerated by editing dataflow.json and then running: ruby www/test/dataflow.cgi -->|
    deplist.each do |path, entry|
      next if path !~ /whimsy.apache.org\/public/
      out.puts %Q|<dt>#{File.basename(path)}</dt>|
      out.puts %Q|  <dd>#{entry['description']} (<a href="#{DATAFLOWDOC}#{path}">docs</a>)</dd>|
    end
    out.puts %Q|</dl><br/>For more information <a href="https://whimsy.apache.org/docs/">see API docs</a>|
    out.puts %Q|and the <a href="https://github.com/apache/whimsy/blob/master/DEPLOYMENT.md#configuration-locations">public JSON generator scripts</a>.|
  end
  exit
end

require 'whimsy/asf'
require 'wunderbar'
require 'wunderbar/bootstrap'
GITWHIMSY = 'https://github.com/apache/whimsy/blob/master'

_html do
  _body? do
    _whimsy_body(
      title: PAGETITLE,
      related: {
        "https://projects.apache.org/" => "Apache Projects Listing",
        "https://home.apache.org/" => "Apache Committer Phonebook",
        "https://community.apache.org/" => "Apache Community Development",
        "/public" => "Whimsy public JSON datafiles",
        "/docs" => "Whimsy code developer documentation"
      },
      helpblock: -> {
        _p %{ Whimsy tools consume and produce a variety of data files
          about PMCs and the ASF as a whole.  This non-comprehensive
          page explains which tools generate what intermediate data,
          and where the canonical underlying data sources are (many
          of which are privately stored). .json files generated in
          /public are consumed by many other websites.
        }
        _p do
          _ %{ Whimsy has a number of cron jobs - typically hourly -
            that periodically regenerate the /public directory, but
            only when the underlying data source has changed.
            See the
          }
          _a 'server setup docs for more info.', href: 'https://github.com/apache/whimsy/blob/master/DEPLOYMENT.md'
          _ ' You can see the '
          _a 'code for this script', href: "#{GITWHIMSY}/www#{ENV['SCRIPT_NAME']}"
          _ ', the '
          _a 'underlying data file', href: "#{GITWHIMSY}/www/test/#{DATAFLOWDATA}"
          _ ', the '
          _a 'key to this data', href: "#datakey"
          _ ', and many of the '
          _a 'public JSON data files.', href: "/public"
        end
        _p do
          _span.text_warning 'REMINDER:'
          _ %{ These datafiles are not original sources of truth, and
            merely make data from other canonical systems available in a more
            easily digested format on a periodic basis.  Data here may be
            outdated depending on when updates were last made.
          }
          _a 'See notifications@whimsical for updates', href: 'https://lists.apache.org/list.html?notifications@whimsical.apache.org'
        end
      }
    ) do
      _ul.list_group do
        deplist.each do |dep, info|
          _li.list_group_item do
            _a '', name: dep.gsub(/[#%\[\]\{\}\\"<>]/, '')
            if dep =~ /http/i then
              _code! do
                _a! File.basename(dep), href: dep
              end
            elsif dep =~ %r{\A/} then
              _code! do
                _a! dep, href: "#{GITWHIMSY}#{dep}"
              end
            else
              _code! dep
            end
            _ " #{info['description']}"
            _br
            if info['maintainer'] =~ %r{/} then
              _span.text_muted 'Maintained by Whimsy PMC using script: '
              _a.text_muted info['maintainer'], href: "#{GITWHIMSY}#{info['maintainer']}"
            else
              _span.text_muted 'Maintained by role/PMC: '
              _a.text_muted info['maintainer'], href: "/foundation/orgchart/#{info['maintainer']}"
            end
            _br
            if info.key?('format') then
              _span "Data structure: #{info['format']}"
              _br
            end
            if info.key?('sources') then
              _span 'Derived from:'
              _ul do
                info['sources'].each do |src|
                  _li do
                    _a src, href: "##{src.gsub(/[#%\[\]\{\}\\"<>]/, '')}"
                  end
                end
              end
            end
          end
        end
      end
      _p do
        _a '', name: 'datakey'
        _ "The #{DATAFLOWDATA} file is currently a manually maintained file where the hash key identifies a file: "
        _ul do
          _li "Starting with 'http' means it's at a public URL"
          _li "Starting with '/' means it's a path within whimsy repo"
          _li "All other paths means it's an SVN/Git reference from repository.yml"
        end
        _ul do
          _li "Maintainers starting with '/' are a path to a script"
          _li "All other maintainers are a role or PMC"
        end
      end
    end
  end
end

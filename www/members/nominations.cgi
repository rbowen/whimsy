#!/usr/bin/env ruby
PAGETITLE = "New Member nominations cross-check" # Wvisible:meeting
$LOAD_PATH.unshift '/srv/whimsy/lib'

require 'erb'
require 'mail'
require 'wunderbar/bootstrap'
require 'whimsy/asf'
require 'whimsy/asf/nominated-members'
require_relative 'meeting-util'

# link to members private-arch
MBOX = 'https://mail-search.apache.org/members/private-arch/members/'

# link to roster page
ROSTER = '/roster/committer'
MEETINGS = ASF::SVN['Meetings']
MAIL_ROOT = '/srv/mail' # TODO: this should be config item

# Encapsulate gathering data to improve error processing
def setup_data
  # get a list of current year's members@ emails
  year = Time.new.year.to_s
  archive = Dir[File.join(MAIL_ROOT, "members", "#{year}*", "*")]

  # select messages that have a subject line starting with [MEMBER NOMINATION]
  emails = []
  archive.each do |email|
    next if email.end_with? '/index'
    message = IO.read(email, mode: 'rb')
    next unless message[/^Date: .*/].to_s.include? year
    subject = message[/^Subject: .*/]
    next if not subject # HACK: allow script to continue if bogus email
    subjectUC = subject.upcase
    next unless subjectUC =~ /MEMBER/
    next unless subjectUC =~ /NOMI[NM]ATION/
    next if subject =~ /Member nominations: a plea/ # not a nomination!
    mail = Mail.new(message.encode(message.encoding, crlf_newline: true))
    next if mail.subject.downcase == 'member nomination process'
    emails << mail if mail.subject =~ /^\[?MEMBER(SHIP)? NOMI[MN]ATION\]?/i
  end

  # parse nominations for names and ids
  nominations = ASF::MemberFiles.member_nominees.map do |id, hash|
    {id: id, name: hash['Public Name']}
  end

  # preload names
  people = ASF::Person.preload('cn',
    nominations.map {|nominee| ASF::Person.find(nominee[:id])})

  return nominations, people, emails
end

# produce HTML output of reports, highlighting ones that have not (yet)
# been posted
_html do
  _style %{
    .missing {background-color: yellow}
    .flexbox {display: flex; flex-flow: row wrap}
    .flexitem {flex-grow: 1}
    .flexitem:first-child {order: 2}
    .flexitem:last-child {order: 1}
    .count {margin-left: 4em}
  }
  _body? do
    _whimsy_body(
      title: PAGETITLE,
      related: {
        '/members/memberless-pmcs' => 'PMCs with no/few ASF Members',
        '/members/watch' => 'Watch list for potential Member candidates',
        ASF::SVN.svnpath!('Meetings') => 'Official Meeting Agenda Directory'
      },
      helpblock: -> {
        _ 'This script checks new member nomination statements from members@ against the official meeting ballot files, and highlights differences. '
        _ 'This probably only works in the period shortly before or after a Members meeting!'
        _br
        _ 'Entries are highlighted if they are not present in both lists.'
      }
    ) do
      cur_mtg_dir = File.basename(MeetingUtil.get_latest(MEETINGS))
      nominations, people, emails = setup_data
      _div.flexbox do
        _div.flexitem do
          _h1_! do
            _a 'Nominees', href: 'watch/nominees'
            _ ' in '
            _a 'svn', href: ASF::SVN.svnpath!('Meetings', cur_mtg_dir, 'nominated-members.txt')
          end

          _p.count "Count: #{nominations.count}"

          _ul nominations.sort_by {|nominee| nominee[:name]} do |nominee|
            _li! do
              person = ASF::Person.find(nominee[:id])
              # N.B. \b does not match if it follows ')', so won't match John (Fred)
              # TODO: Work-round is to also look for EOS, but this needs to be improved
              match = /\b(#{Regexp.escape(nominee[:name]||'')}|#{Regexp.escape(person.public_name||'')})(\b|$)/i

              if emails.any? {|mail| mail.subject.downcase =~ match}
                _a.present person.public_name, href: "#{ROSTER}/#{nominee[:id]}"
              else
                _a.missing person.public_name, href: "#{ROSTER}/#{nominee[:id]}"
              end

              if nominee[:name] != person.public_name
                _span " (as #{nominee[:name]})"
              end
            end
          end
        end

        nominees = nominations.map! {|person| person[:name]}
        nominees += people.map {|person| person.public_name}

        _div.flexitem do
          _h1_.posted! do
            _a "Posted", href:
              'https://mail-search.apache.org/members/private-arch/members/'
            _ " nominations reports"
          end

          _p.count "Count: #{emails.count}"

          # attempt to sort reports by nominee name
          emails.sort_by! do |mail|
            mail.subject.downcase.gsub('- ', '').sub(/\[.*?\]\s*/, '')
          end

          # output an unordered list of subjects linked to the message archive
          _ul emails do |mail|
            _li do
              # ERB::Util.url_encode changes space to %20 as required in the path component
              href = MBOX + mail.date.strftime('%Y%m') + '.mbox/' +
              ERB::Util.url_encode('<' + mail.message_id + '>')

              # N.B. \b does not match if it follows ')', so won't match John (Fred)
              # TODO: Work-round is to also look for EOS, but this needs to be improved
              if nominees.any? {|name| mail.subject =~ /\b#{Regexp.escape(name)}(\b|$)/i}
                _a.present mail.subject, href: href
              else
                _a.missing mail.subject, href: href
                _ ' From: '
                _ mail.from.first
              end
            end
          end
        end
      end
    end
  end
end

# produce JSON output of reports
# N.B. This is activated if the ACCEPT header references 'json'
_json do
  _ reports do |mail| # TODO: reports is not defined
    _subject mail.subject
    _link MBOX + ERB::Util.url_encode('<' + mail.message_id + '>') # TODO looks wrong: does not agree with href above
    _missing missing.any? {|title| mail.subject.downcase =~ /\b#{Regexp.escape(title)}\b/}
  end
end

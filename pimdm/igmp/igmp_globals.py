# IGMP timers (in seconds)
RobustnessVariable = 2
QueryInterval = 125
QueryResponseInterval = 10
MaxResponseTime_QueryResponseInterval = QueryResponseInterval*10
GroupMembershipInterval = RobustnessVariable * QueryInterval + QueryResponseInterval
OtherQuerierPresentInterval = RobustnessVariable * QueryInterval + QueryResponseInterval/2
StartupQueryInterval = QueryInterval / 4
StartupQueryCount = RobustnessVariable
LastMemberQueryInterval = 1
MaxResponseTime_LastMemberQueryInterval = LastMemberQueryInterval*10
LastMemberQueryCount = RobustnessVariable
UnsolicitedReportInterval = 10
Version1RouterPresentTimeout = 400

# IGMP msg type
Membership_Query = 0x11
Version_1_Membership_Report = 0x12
Version_2_Membership_Report = 0x16
Leave_Group = 0x17
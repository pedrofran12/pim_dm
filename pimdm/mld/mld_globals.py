#MLD timers (in seconds)
RobustnessVariable = 2
QueryInterval = 125
QueryResponseInterval = 10
MulticastListenerInterval = (RobustnessVariable * QueryInterval) + (QueryResponseInterval)
OtherQuerierPresentInterval = (RobustnessVariable * QueryInterval) + 0.5 * QueryResponseInterval
StartupQueryInterval = (1/4) * QueryInterval
StartupQueryCount = RobustnessVariable
LastListenerQueryInterval = 1
LastListenerQueryCount = RobustnessVariable
UnsolicitedReportInterval = 10


# MLD msg type
MULTICAST_LISTENER_QUERY_TYPE = 130
MULTICAST_LISTENER_REPORT_TYPE = 131
MULTICAST_LISTENER_DONE_TYPE = 132
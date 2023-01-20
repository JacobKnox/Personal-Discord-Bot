# Personal Discord Bot
## Notation
- "()" indicates an optional parameter
- "[]" indicates a required parameter
## Admin Commands
### !clearlog
Clears the command logs
### !shutoff
Shuts the bot off
### !restart
Restarts the bot
### !work \[clock\]
- clock: accepts "start" or "stop", which indicates whether to "clock in" or "clock out"
### !addserver (guild_id)
Adds a server to the list of permitted servers
- guild_id: Id of the server to add. If not specified, defaults to the id of the server the command was used in.
## [Politics and War](https://politicsandwar.com/) Commands
### !pnwinfra \[start\] \[end\] (nation_id)
Calculates the cost to go from start infra level to end infra level
- nation_id: Optionally specify a nation id to get the specific cost for that nation (takes into account projects and policies)
- start: The infra level to start at
- end: The infra level to end at
### !pnwland \[start\] \[end\] (nation_id)
Calculates the cost to go from start land level to end land level
- nation_id: Optionally specify a nation id to get the specific cost for that nation (takes into account projects and policies)
- start: The land level to start at
- end: The land level to end at
### !pnwcity \[start\] \[end\] (nation_id)
Calculates the cost to go from start city to end city
- start: The city to start at
- end: The city to end at
- nation_id: Optionally specify a nation id to get the specific cost for that nation (takes into account projects and policies)
### !pnwfood \[nation_id\]
Calculates the food production, usage, and net revenue for a nation
- nation_id: The nation whose food information is to be calculated
### !pnwraw \[nation_id\] \[resource\]
Calculates the production, usage, and net revenue of a given raw resource for a nation
- nation_id: The nation whose coal information is to be calculated
- resource: The raw resource to calculate
### !pnwmanu \[nation_id\] \[resource\]
Calculates the production, usage, and net revenue of a given manufactured resource for a nation
- nation_id: The nation whose iron information is to be calculated
- resource: The manufactures resource to calculate
build:
	-docker build -t indy-agent .

start:
	-docker run -it -p $$PORT:$$PORT -e PORT=$$PORT --name indy-agent_$$PORT indy-agent
	-docker rm indy-agent_$$PORT

getip:
	-docker container inspect indy-agent_$$PORT | grep "\"IPAddress\"" | tail -n 1 | sed "s/[IPAddress|:|\"|,| ]//g"

# Shared dict of server_path -> subprocess.Popen
# Both ServersView (writes) and ConsoleView (reads) import this.
running_processes = {}

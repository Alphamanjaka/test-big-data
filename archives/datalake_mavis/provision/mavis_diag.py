import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("102.16.7.154", port=8090, username="mmtadmin",
            password="rkt20mc!", timeout=30, allow_agent=False,
            look_for_keys=False)

def run(c):
    print("==== CMD:", c)
    _, stdout, stderr = ssh.exec_command(c, timeout=90)
    print(stdout.read().decode(errors="replace").strip())
    e = stderr.read().decode(errors="replace").strip()
    if e: print("STDERR:", e)

run("echo 'rkt20mc!' | sudo -S tail -50 /var/log/postgresql/postgresql-14-main.log 2>&1")
ssh.close()
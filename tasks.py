from invoke import task


@task
def dk_up(c):
    c.run("docker compose up -d  --build")


@task
def dk_up_fg(c):
    c.run("docker compose up --build")


@task
def dk_down(c):
    c.run("docker compose down")


@task
def dk_logs(c):
    c.run("docker compose logs")

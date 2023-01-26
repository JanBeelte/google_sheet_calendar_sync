from invoke import task


@task
def dk_save(c):
	c.run("docker save --output google_sync.tar google_sync-google_sync")

	
@task
def dk_load(c):
	c.run("docker load --input google_sync.tar")

	
@task(dk_save)
def dk_copy(c):
	c.run("scp tasks.py hetzner5:jbeelte/google_sync")
	c.run("scp docker-compose-deploy.yml hetzner5:jbeelte/google_sync/docker-compose.yml")
	c.run("scp google_sync.tar hetzner5:jbeelte/google_sync")
